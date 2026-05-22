"""VideoMObject: a Manim mobject that represents an embedded video clip.

The :class:`VideoMObject` is a ``Rectangle`` sub-class that acts as a visual
placeholder for a video clip in a Manim scene.  The clip itself is **not**
rendered frame-by-frame; instead, it is composited onto the rendered partial
movie file by :class:`~manim_videos.animations.OverlayVideo` at render time,
which is far more efficient than converting to ImageMobjects.

Example::

    from moviepy import VideoFileClip
    from manim_videos import VideoMObject

    clip = VideoFileClip("my_video.mp4").subclipped(0, 5)
    vid = VideoMObject(clip)
    vid.stretch_to_keep_aspect()
"""

from __future__ import annotations

from functools import partial
from pathlib import Path
from typing import Self

import numpy as np
import numpy.typing as npt
from manim import (
    DL,
    DR,
    RIGHT,
    UL,
    UR,
    WHITE,
    Group,
    ImageMobject,
    ManimColor,
    Rectangle,
    VMobject,
    angle_of_vector,
)
from moviepy import VideoFileClip


class VideoMObject(VMobject):
    """A Manim mobject that embeds a video clip in a scene.

    Internally, a :class:`VideoMObject` is a :class:`~manim.VMobject` container
    that acts as a visual placeholder for a video clip. It contains a border
    rectangle and a text label for visualization during the "Manim pass".
    The actual video frames are composited onto the rendered output by
    :class:`~manim_videos.animations.OverlayVideo`.

    Compositing effects are driven by the state of this mobject during the
    :class:`~manim_videos.animations.OverlayVideo` animation:

    * **Rounded corners** — call :meth:`round_corners` (or animate
      :attr:`corner_radius` via ``always_redraw``) before/during the play
      call. The radius is sampled each frame and converted to a pixel-space
      alpha mask during compositing.
    * **Opacity / fade** — pair :class:`~manim_videos.animations.OverlayVideo`
      with :class:`~manim.FadeIn` or :class:`~manim.FadeOut`. The mobject's
      ``stroke_opacity`` is sampled each frame and applied as a uniform
      alpha multiplier on the composited clip::

          self.play(OverlayVideo(vid), FadeIn(vid))
          self.play(OverlayVideo(vid), FadeOut(vid))

    .. note::
        The clip object is held via a closure inside :meth:`get_clip` rather
        than as a plain instance attribute. This prevents Manim's caching
        system from hashing randomly-generated subprocess attributes (e.g. the
        FFMPEG PID) and breaking the animation cache.

    Args:
        clip: Either a :class:`moviepy.VideoFileClip` instance or a path (str
            or :class:`pathlib.Path`) to a video file.
        width: Width of the video object. Default 4.0.
        height: Height of the video object. Default 2.0.
        stroke_width: Width of the video object border. Defaults to
            ``0`` (no border) so the clip replaces it completely.
        stroke_color: Color of the video object border. Defaults to
            ``WHITE``.
        **kwargs: Keyword arguments forwarded to :class:`~manim.VMobject`.

    Example::

        vid = VideoMObject("clip.mp4", width=6, height=3.375)
        vid.stretch_to_keep_aspect()
    """

    def __init__(
        self,
        clip: VideoFileClip | str | Path,
        width: float = 4.0,
        height: float = 2.0,
        stroke_width: float = 0,
        stroke_color: ManimColor = WHITE,
        **kwargs,
    ) -> None:
        super().__init__(fill_opacity=0, stroke_width=0, **kwargs)

        if isinstance(clip, (str, Path)):
            clip = VideoFileClip(str(clip))

        # IMPORTANT: Here we capture a reference to the clip object via a closure, this enables us to access
        #   the clip by calling `get_clip` yet does not directly put the clip in the `__dict__` attribute.
        #   Manim hashes objects by hashing their `__dict__`'s recursively and `clip.reader.proc` is a
        #   subprocess to FFMPEG which contains attributes like the PID which are randomly generated.
        #   If not careful and these are allowed to be hashed, then two identical clips will have different hashes.
        # On the other hand: Currying the clip like below means that the actual clip contents are not hashed, only
        #   it's "manin-style" attributes such as size, position, and clip filename since it's added to self.
        #   For instance if you render a VideoMObject of a subclip (0-1) and change it to (1-2)
        #   it will think it was already cached! Other attrs might cause similar issues...
        self.get_clip = partial(lambda: clip)

        # Initialize rectangle geometry
        self.start_new_path(UR)
        self.add_points_as_corners([UL, DL, DR, UR])
        self.close_path()
        self.stretch_to_fit_width(width)
        self.stretch_to_fit_height(height)

        # Hidden anchor to track the 4 sharp corners through all transformations
        self._corners_anchor = VMobject(stroke_opacity=0).set_points([self.get_corner(d) for d in [UR, UL, DL, DR]])
        self.add(self._corners_anchor)

        self.border = Rectangle(
            width=width,
            height=height,
            stroke_width=stroke_width,
            stroke_color=stroke_color,
            fill_opacity=0,
            stroke_opacity=1,
        ).move_to(self.get_center())
        self.add(self.border)

        self.filename = getattr(clip, "filename", None)
        self.corner_radius = 0

    @property
    def duration(self) -> float:
        """The total duration of the embedded video clip (in seconds)."""
        return float(self.get_clip().duration)

    @property
    def angle(self) -> float:
        """The current rotation angle of the mobject (in radians)."""
        tr, tl, _bl, _br = self.get_ordered_corners()
        return angle_of_vector(tr - tl) - angle_of_vector(RIGHT)

    def get_ordered_corners(self) -> npt.NDArray:
        """Return the "sharp" corners of the video in counter-clockwise order, even if ``reverse_direction`` was called."""
        return self._corners_anchor.points

    def round_corners(self, radius: float) -> Self:
        """Round the corners of the composited video clip and its border.

        Sets :attr:`corner_radius` to *radius* and applies
        ``round_corners(radius)`` to the border rectangle so that the visual
        placeholder matches the composited result.

        During compositing, :class:`~manim_videos.animations.OverlayVideo`
        samples :attr:`corner_radius` each frame and converts it to a
        pixel-space rounded-rectangle alpha mask that is applied to the clip.
        This means the radius can be animated — for example using
        ``always_redraw`` with a :class:`~manim.ValueTracker`::

            radius = ValueTracker(0)
            video = always_redraw(
                lambda: VideoMObject(clip)
                    .stretch_to_keep_aspect()
                    .round_corners(radius.get_value())
            )
            self.play(OverlayVideo(video), radius.animate.set_value(0.5))

        Args:
            radius: Corner radius in Manim scene units.

        Returns:
            ``self``, for method chaining.
        """
        self.corner_radius = radius
        self.border.round_corners(radius)
        return self

    def become(self, mobject, *args, **kwargs) -> Self:
        """Copy custom attributes that Manim's default ``become`` does not propagate."""
        result = super().become(mobject, *args, **kwargs)
        if isinstance(mobject, VideoMObject):
            self.corner_radius = mobject.corner_radius
        return result

    def stretch_to_keep_aspect(self, keep_dim: int = 0) -> Self:
        """Resize the placeholder to match the clip's native aspect ratio.

        Args:
            keep_dim: Which dimension to keep fixed:
                - ``0``: keep the current *width*, adjust height.
                - ``1``: keep the current *height*, adjust width.

        Returns:
            ``self``, for method chaining.

        Raises:
            ValueError: If *keep_dim* is not ``0`` or ``1``.
        """
        h, w = self.get_clip().h, self.get_clip().w

        if keep_dim == 0:
            self.stretch_to_fit_height(self.width * h / w)
        elif keep_dim == 1:
            self.stretch_to_fit_width(self.height * w / h)
        else:
            raise ValueError(f"Argument `keep_dim` can only be 0 (width) or 1 (height), got {keep_dim}.")

        return self

    def get_frame(self, t: float, border: bool = False) -> Group | ImageMobject:
        """Return the video frame at time *t*.

        Args:
            t: Time in seconds within the clip.
            border: Whether to include the border rectangle. Defaults to ``False``.

        Returns:
            The decoded frame as an :class:`~manim.ImageMobject`, optionally
            inside a :class:`~manim.Group` with the border.
        """
        clip = self.get_clip()
        frame_arr = clip.get_frame(t=t)

        if clip.mask:
            mask = clip.mask.get_frame(t=t) * 255
            frame_arr = np.dstack((frame_arr, mask.astype(np.uint8)))

        frame = ImageMobject(frame_arr)

        # Align frame to the current geometry of the placeholder
        frame.stretch_to_fit_width(self.width)
        frame.stretch_to_fit_height(self.height)
        frame.move_to(self.get_center())
        frame.rotate(self.angle)

        if border:
            return Group(self.border.copy(), frame)

        return frame

    def get_first_frame(self, border: bool = False) -> Group | ImageMobject:
        """Return the first frame of the clip.

        Args:
            border: Whether to include the border rectangle. Defaults to ``False``.

        Returns:
            The first frame of the clip.
        """
        clip = self.get_clip()
        return self.get_frame(clip.start, border=border)

    def get_last_frame(self, border: bool = False) -> Group | ImageMobject:
        """Return the last frame of the clip.

        Args:
            border: Whether to include the border rectangle. Defaults to ``False``.

        Returns:
            The last frame of the clip.
        """
        clip = self.get_clip()
        return self.get_frame(clip.end - 1 / clip.fps, border=border)
