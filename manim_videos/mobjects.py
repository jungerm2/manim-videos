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

from manim import GRAY, RED, Group, ImageMobject, ManimColor, Rectangle, Text
from moviepy import VideoFileClip


class VideoMObject(Rectangle):
    """A Manim mobject that embeds a video clip in a scene.

    Internally, a :class:`VideoMObject` is a coloured :class:`~manim.Rectangle`
    that shows a text label (the clip filename) as a placeholder during the
    "Manim pass".  The actual video frames are composited onto the rendered
    output by :class:`~manim_videos.animations.OverlayVideo`.

    .. note::
        The clip object is held via a closure inside :meth:`get_clip` rather
        than as a plain instance attribute. This prevents Manim's caching
        system from hashing randomly-generated subprocess attributes (e.g. the
        FFMPEG PID) and breaking the animation cache.

    Args:
        clip: Either a :class:`moviepy.VideoFileClip` instance or a path (str
            or :class:`pathlib.Path`) to a video file.
        *args: Positional arguments forwarded to :class:`~manim.Rectangle`.
        stroke_width: Width of the placeholder rectangle border. Defaults to
            ``0`` (no border) so the clip replaces it completely.
        fill_color: Fill colour of the placeholder. Defaults to ``GRAY``.
        fill_opacity: Opacity of the placeholder fill. Defaults to ``1.0``.
        **kwargs: Keyword arguments forwarded to :class:`~manim.Rectangle`.

    Example::

        vid = VideoMObject("clip.mp4", width=6, height=3.375)
        vid.stretch_to_keep_aspect()
    """

    def __init__(
        self,
        clip: VideoFileClip | str | Path,
        *args,
        stroke_width: float = 0,
        fill_color: ManimColor = GRAY,
        fill_opacity: float = 1.0,
        **kwargs,
    ) -> None:
        super().__init__(*args, stroke_width=stroke_width, fill_color=fill_color, fill_opacity=fill_opacity, **kwargs)

        if isinstance(clip, (str, Path)):
            clip = VideoFileClip(str(clip))

        # IMPORTANT: Here we capture a reference to the clip object via a closure, this enables us to access
        #   the clip by calling `get_clip` yet does not directly put the clip in the `__dict__` attribute.
        #   Manim hashes objects by hashing their `__dict__`'s recursively and `clip.reader.proc` is a
        #   subprocess to FFMPEG which contains attributes like the PID which are randomly generated.
        #   If not careful and these are allowed to be hashed, then two identical clips will have different hashes.
        # On the other hand: Currying the clip like below means that the actual clip contents are not hashed, only
        #   it's "manin-style" attributes such as size, position, and clip filename since it's added to self via
        #   self.text below. For instance if you render a VideoMObject of a subclip (0-1) and change it to (1-2)
        #   it will think it was already cached! Other attrs might cause similar issues...
        self.get_clip = partial(lambda: clip)

        self.text = Text(f"Video clip of:\n{clip.filename}", color=RED).move_to(self.get_center())
        self.text.scale_to_fit_width(self.width * 0.95)
        self.add(self.text)

    @property
    def duration(self) -> float:
        """The total duration of the embedded video clip (in seconds)."""
        return float(self.get_clip().duration)

    def stretch_to_keep_aspect(self, keep_dim: int = 0) -> VideoMObject:
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
        self.remove(self.text)

        if keep_dim == 0:
            self.stretch_to_fit_height(self.width * h / w)
        elif keep_dim == 1:
            self.stretch_to_fit_width(self.height * w / h)
        else:
            raise ValueError(f"Argument `keep_dim` can only be 0 (width) or 1 (height), got {keep_dim}.")

        self.text.scale_to_fit_width(self.width * 0.95)
        self.add(self.text)
        return self

    def get_border(self) -> Rectangle:
        """Return a :class:`~manim.Rectangle` matching the current size and stroke of the video."""
        return (
            Rectangle()
            .stretch_to_fit_width(self.width)
            .stretch_to_fit_height(self.height)
            .move_to(self.get_center())
            .set_stroke(self.stroke_color, self.stroke_opacity)
        )

    def get_frame(self, t: float, border: bool = False) -> Group | ImageMobject:
        """Return the video frame at time *t*.

        Args:
            t: Time in seconds within the clip.
            border: Whether to include the border rectangle. Defaults to ``False``.

        Returns:
            The decoded frame as an :class:`~manim.ImageMobject`, optionally
            inside a :class:`~manim.Group` with the border.
        """
        frame = (
            ImageMobject(self.get_clip().get_frame(t=t))
            .stretch_to_fit_width(self.width)
            .stretch_to_fit_height(self.height)
            .move_to(self.get_center())
        )

        if border:
            return Group(self.get_border(), frame)

        return frame

    def get_first_frame(self, border: bool = False) -> Group | ImageMobject:
        """Return the first frame of the clip.

        Args:
            border: Whether to include the border rectangle. Defaults to ``False``.

        Returns:
            The first frame of the clip.
        """
        return self.get_frame(0, border=border)

    def get_last_frame(self, border: bool = False) -> Group | ImageMobject:
        """Return the last frame of the clip.

        Args:
            border: Whether to include the border rectangle. Defaults to ``False``.

        Returns:
            The last frame of the clip.
        """
        clip = self.get_clip()
        return self.get_frame(clip.end - 1 / clip.fps, border=border)
