"""VideoMixin: a mixin that enables video overlaying in Manim scenes and Slides.

Mix :class:`VideoMixin` into any :class:`~manim.Scene` (or
:class:`~manim_slides.Slide`) subclass to enable automatic compositing of
:class:`~manim_videos.animations.OverlayVideo` animations.

Usage with plain Manim::

    from manim import *
    from manim_videos import VideoMixin, VideoMObject

    class MyScene(VideoMixin, Scene):
        def construct(self):
            vid = VideoMObject("clip.mp4")
            self.next_section()
            self.add(vid)
            self.play(vid.play())
            self.next_section()

Usage with Manim Slides (requires ``manim-slides`` to be installed)::

    from manim import *
    from manim_slides import Slide
    from manim_videos import VideoMixin, VideoMObject

    class MySlide(VideoMixin, Slide):
        def construct(self):
            vid = VideoMObject("clip.mp4")
            self.next_slide(loop=True)
            self.add(vid)
            self.play(vid.play())
"""

from __future__ import annotations

import os
from ast import literal_eval

from manim import config
from manim.utils.parameter_parsing import flatten_iterable_parameters

from manim_videos.animations import OverlayVideo


class VideoMixin:
    """Mixin that adds video-overlay support to a Manim scene.

    Override ``play()`` to intercept :class:`~manim_videos.animations.OverlayVideo`
    animations, hide their placeholder rectangles during rendering, invoke the
    normal Manim rendering pipeline, and then call each animation's
    :meth:`~manim_videos.animations.OverlayVideo.finalize` to composite the
    actual video clip onto the output.

    .. note::
        ``manim-slides`` is *not* a hard dependency of this library.  If you
        wish to use :class:`VideoMixin` with a
        :class:`~manim_slides.Slide`-based class, install it separately.

    .. note::
        Compositing is done sequentially, ordered by the ``z_index`` of each
        :class:`~manim_videos.mobjects.VideoMObject`.  Multiple overlapping
        videos in the same ``play()`` call are supported, but videos should be
        of the same duration.

    Environment:
        Set ``SKIP_VIDEO_OVERLAY=True`` to bypass all compositing (useful for
        fast preview renders).
    """

    def play(self, *args, **kwargs) -> None:
        """Play animations, compositing any video overlays afterwards.

        Finds all :class:`~manim_videos.animations.OverlayVideo` instances
        among the arguments, makes their placeholder rectangles invisible,
        delegates to the parent ``play()`` implementation, and then calls
        :meth:`~manim_videos.animations.OverlayVideo.finalize` on each one in
        ``z_index`` order.

        Args:
            *args: Animations (or iterables of animations) to play.
            **kwargs: Keyword arguments forwarded to the parent ``play()``.
        """
        if literal_eval(os.environ.get("SKIP_VIDEO_OVERLAY", "False")):
            return super().play(*args, **kwargs)

        overlays: list[OverlayVideo] = sorted(
            filter(lambda a: isinstance(a, OverlayVideo), flatten_iterable_parameters(args)),
            key=lambda a: a.video_mobject.z_index,
        )

        for anim in overlays:
            anim.video_mobject.set_fill(opacity=0.0, color=config.background_color)
            anim.video_mobject.set_stroke(opacity=0.0, color=config.background_color)

        super().play(*args, **kwargs)

        for anim in overlays:
            anim.finalize()
