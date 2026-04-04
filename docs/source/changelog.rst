Changelog
=========

Unreleased
----------

Features:
    * :class:`~manim_videos.VideoMObject.get_frame` now respects video masks.
    * Add :class:`~manim_videos.VideoMObject.angle`, :class:`~manim_videos.VideoMObject.get_ordered_vertices` methods.

Bug fixes:
    * Fixed VideoMObject border not properly hiding during video overlay.
    * Fixed output video's fps to be that of manim's config.

v0.1.0 (2026-03-30)
-------------------

* :class:`~manim_videos.VideoMObject`: video placeholder mobject.
* :class:`~manim_videos.OverlayVideo`: compositing animation.
* :class:`~manim_videos.VideoMixin`: scene/slide mixin.
* ``SKIP_VIDEO_OVERLAY`` environment variable for fast preview renders.
