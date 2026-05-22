"""OverlayVideo: an animation that composites a video clip onto rendered output.

:class:`OverlayVideo` extends Manim's :class:`~manim.Wait` animation and uses
a post-render hook (:meth:`clean_up_from_scene`) to retrieve the path of the
partial movie file that Manim just wrote.  After the scene's ``play()`` call
returns, :meth:`finalize` composites the video clip onto that file using
*moviepy*, replacing it in-place.
"""

from __future__ import annotations

import functools
import itertools
import os
import warnings
from functools import partial
from pathlib import Path

import numpy as np
from manim import Scene, Wait, config
from moviepy import CompositeVideoClip, ImageClip, VideoClip, VideoFileClip, vfx
from PIL import Image, ImageDraw

from manim_videos.mobjects import VideoMObject


class OverlayVideo(Wait):
    """A ``Wait`` animation that composites a video clip at render time.

    When used inside a :class:`~manim_videos.mixins.VideoMixin` scene, the
    animation renders a transparent/background-coloured placeholder rectangle
    during Manim's normal rendering pass and then composites the real video
    clip onto the produced partial movie file (via *moviepy*) in a
    post-processing step.

    Args:
        video_mobject: The :class:`~manim_videos.mobjects.VideoMObject` whose
            clip should be composited.
        *args: Positional arguments forwarded to :class:`~manim.Wait`.
        **kwargs: Keyword arguments forwarded to :class:`~manim.Wait`.

    Note:
        The ``run_time`` of this animation is automatically set to the clip's
        duration (via :attr:`~manim_videos.mobjects.VideoMObject.duration`) if
        not specified, but can be overridden if needed.
    """

    def __init__(
        self,
        video_mobject: VideoMObject,
        run_time: float | None = None,
        frozen_frame: bool = False,
        **kwargs,
    ) -> None:
        if run_time is None:
            run_time = video_mobject.duration

        self.video_mobject = video_mobject
        self.section_paths: list[str] = []
        self.skip_animations: bool = False
        self._ts: list[float] = []
        self._corners: list[np.ndarray] = []
        self._radii: list[float] = []
        super().__init__(run_time, frozen_frame=frozen_frame, **kwargs)

    def interpolate(self, alpha: float) -> None:
        super().interpolate(alpha)
        self._ts.append(alpha)
        self._corners.append(self.video_mobject.get_ordered_corners())
        self._radii.append(self.video_mobject.corner_radius)

    @staticmethod
    def coords_to_pix(scene: Scene, point: np.ndarray) -> np.ndarray:
        """Convert Manim scene coordinates to pixel coordinates.

        Manim uses a Cartesian coordinate system centred at the scene origin,
        while *moviepy* (and most image libraries) use a top-left origin with
        the Y-axis pointing downwards.  This method applies the necessary
        scaling and inversion.

        Args:
            scene: The current :class:`~manim.Scene` instance.
            point: A 3-element array ``[x, y, z]`` in scene coordinates.

        Returns:
            A 3-element array ``[px, py, pz]`` in pixel coordinates, where
            ``py`` is measured from the *top* of the frame.
        """
        camera = scene.renderer.camera
        conversion = np.array(
            [
                camera.pixel_width / camera.frame_width,
                -camera.pixel_height / camera.frame_height,
                1,
            ],
        )
        offset = np.array([camera.pixel_width / 2, camera.pixel_height / 2, 0])
        return (point - camera.frame_center) * conversion + offset

    @staticmethod
    def _compute_homography_batched(src_pts: np.ndarray, dst_pts: np.ndarray) -> np.ndarray:
        """Computes homography using the Direct Linear Transformation (DLT) algorithm in a batched manner.

        Args:
            src_pts: (B, N, 2) - B batches, N points, (x, y)
            dst_pts: (B, N, 2) - B batches, N points, (x, y)

        Returns:
            (B, 8) - Batched homography parameters
        """
        B, N, _ = src_pts.shape

        # Construct A matrix (2N x 9) for all batches
        # x' = (h1x + h2y + h3) / (h7x + h8y + h9)
        # y' = (h4x + h5y + h6) / (h7x + h8y + h9)
        x = src_pts[:, :, 0].reshape(B, N, 1)
        y = src_pts[:, :, 1].reshape(B, N, 1)
        xp = dst_pts[:, :, 0].reshape(B, N, 1)
        yp = dst_pts[:, :, 1].reshape(B, N, 1)
        zero = np.zeros((B, N, 1))
        one = np.ones((B, N, 1))
        A1 = np.concatenate([-x, -y, -one, zero, zero, zero, xp * x, xp * y, xp], axis=2)
        A2 = np.concatenate([zero, zero, zero, -x, -y, -one, yp * x, yp * y, yp], axis=2)
        A = np.concatenate([A1, A2], axis=1)

        # U, S, Vh = svd(A) -> h is last row of Vh
        _, _, Vh = np.linalg.svd(A)
        H = Vh[:, -1, :].reshape(B, 9)

        # Normalize H
        return H[:, :-1] / H[:, -1:]

    def clean_up_from_scene(self, scene: Scene) -> None:
        """Hook called by Manim after the animation finishes.

        Captures the scene state needed for compositing: the partial movie file
        path, whether animations are being skipped, and the pixel-space bounds
        of the :class:`~manim_videos.mobjects.VideoMObject`.

        Args:
            scene: The current :class:`~manim.Scene` instance.
        """
        super().clean_up_from_scene(scene)
        self.section_paths = scene.renderer.file_writer.sections[-1].partial_movie_files
        self.skip_animations = scene.renderer.skip_animations

        # Convert Manim coordinates to pixel coordinates
        self._corners = np.array(self._corners)
        self._corners = self.coords_to_pix(scene, self._corners)
        self._radii = np.array(self._radii)
        self._ts = np.array(self._ts)

    def finalize(self) -> None:
        """Composite the video clip onto the rendered partial movie file.

        Selects the correct partial movie file (filtering by duration when
        multiple candidates exist), composites the clip with *moviepy*, and
        replaces the original file in-place.

        If the videomobject's animated, each frame of the clip will be warped
        using an affine or perspective mapping to match the animation. These
        are computed from the 4 corners of the videomobject at each frame.

        Raises:
            RuntimeError: If no suitable partial movie file is found after
                filtering.

        Note:
            When ``skip_animations`` is ``True`` (cached or user-skipped render)
            this method is a no-op.
        """
        if self.skip_animations:
            return

        if len(self.section_paths) > 1:
            duration = self.video_mobject.get_clip().duration
            self.section_paths = [
                p for p in self.section_paths if np.allclose(VideoFileClip(p).duration, duration, rtol=0.05)
            ]
            warnings.warn(
                "Found more than one partial movie file, selecting the one with similar duration as expected.",
                RuntimeWarning,
                stacklevel=2,
            )

        if not self.section_paths:
            raise RuntimeError(
                f"Exactly one partial movie file is needed to overlay video on, "
                f"instead got {self.section_paths}. "
                "Try adding `self.next_section()` before and after the play call.",
            )

        # Load the section video and the video clip
        section_path = self.section_paths[0]
        section_video = VideoFileClip(section_path).with_fps(config.frame_rate)
        clip = self.video_mobject.get_clip().with_fps(config.frame_rate)

        # If the videomobject is not animated, we only need to compute the homography once
        if all(np.allclose(a, b) for a, b in itertools.pairwise(self._corners)):
            self._corners = self._corners[:1]

        # Get the corners of the overlay video clip in CCW order starting from top-right
        # and compute homography mappings from the overlay video clip to the section video (backward mapping)
        clip_corners = np.array(
            [
                [clip.w, 0],
                [0, 0],
                [0, clip.h],
                [clip.w, clip.h],
            ]
        )
        clip_corners = np.repeat(clip_corners[None], len(self._corners), axis=0)
        homographies = self._compute_homography_batched(self._corners[..., :2], clip_corners)

        @functools.cache
        def get_homography(t):
            # It seems the animation is exactly off by one frame, so we add 1/fps
            # to the time here. I have no idea why this occurs yet...
            t += 1 / config.frame_rate

            # If there's only one homography, the scene is static
            if len(homographies) == 1:
                return homographies[0]

            return np.array([np.interp(t / self.run_time, self._ts, param) for param in homographies.T])

        def warp_frame(get_frame, t):
            # Using PIL to warp frames like this is actually what moviepy does under the hood
            # (eg: in rotate, scale, etc.) so it's more efficient (and general) to do it once
            # using a homography than to use moviepy's rotate/scale/etc. methods.
            frame = get_frame(t)
            params = get_homography(t)

            # Small optimization: use affine transform if possible
            if np.allclose(params[-2:], 0):
                method = Image.AFFINE
                params = params[:-2]
            else:
                method = Image.PERSPECTIVE

            # PIL expects uint8 type data. However a mask image has values in the
            # range [0, 1] and is of float type.  To handle this we scale it up by
            # a factor 'a' for use with PIL and then back again by 'a' afterwards.
            a = 255.0 if frame.dtype == "float64" else 1

            return (
                np.array(
                    Image.fromarray((a * frame).astype(np.uint8)).transform(
                        tuple(section_video.size), method, params, resample=Image.Resampling.BILINEAR
                    )
                )
                / a
            )

        def get_inverse_homography(params):
            # Rebuild matrix from params, invert it, normalize it, and return the params
            a, b, c, d, e, f, g, h = params
            H = np.array([a, b, c, d, e, f, g, h, 1])
            H = np.linalg.inv(H.reshape(3, 3))
            H = H.flatten() / H[-1, -1]
            return H[:8]

        def apply_similarity_transform(clip, params):
            # If the homography is a pure translation+scale, use it to set the clip's position/resize
            # We need to invert it first because it's the backward mapping (section -> clip)
            a, b, c, d, e, f, g, h = get_inverse_homography(params)
            clip = clip.with_position((c, f)).resized((clip.w * np.abs(a), clip.h * np.abs(e)))

            if a < 0:
                clip = clip.with_effects([vfx.MirrorX()])
            if e < 0:
                clip = clip.with_effects([vfx.MirrorY()])

            return clip

        def is_similarity_transform(params):
            # Check if the homography is a similarity transform, this works for both the
            # forward/backward mapping since everything except the translation/scale should be eye(3).
            a, b, c, d, e, f, g, h = params
            return np.allclose([b - 1, d - 1, g, h], 0)

        def make_mask(t=None, clip_w=100, clip_h=100):
            # Convert Manim radius to pixel radius and create a rounded rectangle mask
            t += 1 / config.frame_rate  # same fix as above
            radius = np.interp(t / self.run_time, self._ts, self._radii)
            radius_px = int(radius * (clip_w / self.video_mobject.width))
            mask_image = Image.new("L", (clip_w, clip_h), 0)
            draw = ImageDraw.Draw(mask_image)
            draw.rounded_rectangle((0, 0, clip_w - 1, clip_h - 1), radius=radius_px, fill=255)
            return np.array(mask_image) / 255.0

        if np.any(self._radii > 0):
            # Snapshot original clip dimensions before `clip` gets reassigned by
            # with_mask() / transform() later — the closure must use the originals.
            clip_w, clip_h = clip.w, clip.h

            if np.allclose(self._radii, self._radii[0]):
                mask = make_mask(0, clip_w=clip_w, clip_h=clip_h)
                rounded_mask = ImageClip(mask, is_mask=True).with_duration(clip.duration)
            else:
                rounded_mask = VideoClip(
                    frame_function=partial(make_mask, clip_w=clip_w, clip_h=clip_h), is_mask=True
                ).with_duration(clip.duration)

            if clip.mask:
                clip = clip.mask.transform(lambda get_frame, t: get_frame(t) * rounded_mask.get_frame(t))
            else:
                clip = clip.with_mask(rounded_mask)

        if len(homographies) == 1 and is_similarity_transform(homographies[0]):
            clip = apply_similarity_transform(clip, homographies[0])
        else:
            if clip.mask is None:
                clip = clip.with_mask()
            clip = clip.transform(warp_frame, apply_to=["mask"])

        # Write to a temp file then replace, working around a moviepy bug:
        # https://github.com/Zulko/moviepy/issues/1029
        composite = CompositeVideoClip([section_video, clip])
        tmp_path = str(Path(section_path).with_name("temporary_overlay").with_suffix(Path(section_path).suffix))
        composite.write_videofile(tmp_path, fps=config.frame_rate)
        os.replace(tmp_path, section_path)
