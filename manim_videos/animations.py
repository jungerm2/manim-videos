"""OverlayVideo: an animation that composites a video clip onto rendered output.

:class:`OverlayVideo` extends Manim's :class:`~manim.Wait` animation and uses
a post-render hook (:meth:`clean_up_from_scene`) to retrieve the path of the
partial movie file that Manim just wrote.  After the scene's ``play()`` call
returns, :meth:`finalize` composites the video clip onto that file using
*moviepy*, replacing it in-place.
"""

from __future__ import annotations

import os
import warnings
from pathlib import Path

import numpy as np
from manim import UL, Scene, Wait, config
from moviepy import CompositeVideoClip, VideoFileClip

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
        self.upper_left: np.ndarray = np.zeros(2)
        self.width: float = 0.0
        self.height: float = 0.0
        super().__init__(run_time, frozen_frame=frozen_frame, **kwargs)

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
        return (np.array(point) - camera.frame_center) * conversion + offset

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

        right = self.coords_to_pix(scene, self.video_mobject.get_right())
        left = self.coords_to_pix(scene, self.video_mobject.get_left())
        top = self.coords_to_pix(scene, self.video_mobject.get_top())
        btm = self.coords_to_pix(scene, self.video_mobject.get_bottom())
        self.upper_left = self.coords_to_pix(scene, self.video_mobject.get_boundary_point(UL))[:-1]
        self.width = float(abs(right - left)[0])
        self.height = float(abs(top - btm)[1])

    def finalize(self) -> None:
        """Composite the video clip onto the rendered partial movie file.

        Selects the correct partial movie file (filtering by duration when
        multiple candidates exist), composites the clip with *moviepy*, and
        replaces the original file in-place.

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

        section_video = VideoFileClip(self.section_paths[0])
        clip = (
            self.video_mobject.get_clip()
            .resized((int(self.width), int(self.height)))
            .with_position(tuple(self.upper_left))
            .with_fps(int(config["frame_rate"]))
        )
        composite = CompositeVideoClip([section_video, clip])

        # Write to a temp file then replace, working around a moviepy bug:
        # https://github.com/Zulko/moviepy/issues/1029
        original = self.section_paths[0]
        tmp_path = str(Path(original).with_name("temporary_overlay").with_suffix(Path(original).suffix))
        composite.write_videofile(tmp_path)
        os.replace(tmp_path, original)
