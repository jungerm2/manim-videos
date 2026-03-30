"""manim_videos: embed video clips in Manim scenes and Manim Slides presentations.

This library provides three building blocks:

- :class:`~manim_videos.mobjects.VideoMObject` - a Manim ``Rectangle`` sub-class
  that acts as a placeholder for a video clip inside a scene.
- :class:`~manim_videos.animations.OverlayVideo` - a ``Wait``-based animation that
  forces the rendered partial movie file to be the right duration for (later) compositing.
- :class:`~manim_videos.mixins.VideoMixin` - a mixin for ``Scene`` (and optionally
  ``Slide``) that hooks into ``play()`` to trigger the compositing step.
"""

from manim_videos.animations import OverlayVideo
from manim_videos.mixins import VideoMixin
from manim_videos.mobjects import VideoMObject

__all__ = ["OverlayVideo", "VideoMObject", "VideoMixin"]
__version__ = "0.1.0"
