Changelog
=========

Unreleased
----------

Features:
    * :class:`~manim_videos.VideoMObject.get_frame` now respects video masks.
    * Add :attr:`~manim_videos.VideoMObject.angle`, :meth:`~manim_videos.VideoMObject.get_ordered_corners` methods.
    * Support dynamic positioning and transformation animations (such as shift, scale, and rotate) via per-frame homography computation.
    * Add :meth:`~manim_videos.VideoMObject.round_corners` support: corner radius is sampled per-frame and applied as a rounded-rectangle alpha mask during compositing. The radius can be static or animated via ``always_redraw``.
    * Add :class:`~manim.FadeIn` / :class:`~manim.FadeOut` support: :class:`~manim_videos.OverlayVideo` now tracks the :class:`~manim_videos.VideoMObject`'s opacity per-frame and applies it as a uniform alpha multiplier to the composited clip. Running ``FadeIn(vid)`` or ``FadeOut(vid)`` alongside ``OverlayVideo(vid)`` in the same ``play()`` call works transparently.

Bug fixes:
    * Fixed VideoMObject border not properly hiding during video overlay.
    * Fixed output video's fps to be that of manim's config.

v0.1.0 (2026-03-30)
-------------------

* :class:`~manim_videos.VideoMObject`: video placeholder mobject.
* :class:`~manim_videos.OverlayVideo`: compositing animation.
* :class:`~manim_videos.VideoMixin`: scene/slide mixin.
* ``SKIP_VIDEO_OVERLAY`` environment variable for fast preview renders.
