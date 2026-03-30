How it Works
============

The core philosophy of ``manim-videos`` is to avoid decoding video frames
into Manim-managed image arrays (which is slow and CPU-intensive). Instead,
it uses a two-pass approach:

1. **The Manim Pass**: Manim renders the sections normally, and a lightweight
   placeholder for the video clip is instead rendered in the scene.
2. **The Compositing Pass**: A post-render hook uses `<MoviePy https://zulko.github.io/moviepy/>`_ to
   composite the target video file directly onto the rendered partial movie
   files in a single step.

These two steps happen in lockstep for each section of the animation that uses a :class:`~manim_videos.animations.OverlayVideo` animation.

Core Components
---------------

This library provides three main building blocks:

* :class:`~manim_videos.mobjects.VideoMObject`: A :class:`~manim.Rectangle` sub-class that acts as a visual placeholder for a video clip inside your scene. It stores the clip via a closure internally to prevent Manim's caching system from hashing random FFMPEG subprocess attributes.

* :class:`~manim_videos.animations.OverlayVideo`: A :class:`~manim.Wait`-based animation that "reserves" the correct duration in the Manim output. It also captures the camera state (frame size and center) at render time to ensure the video clip is overlayed with correct alignment. Read more about the caching mechanism in :ref:`limitations`.

* :class:`~manim_videos.mixins.VideoMixin`: A mixin for :class:`~manim.Scene` (and optionally :class:`~manim_slides.Slide`) that hooks into the low-level render loop. It detects when an :class:`~manim_videos.animations.OverlayVideo` is performed and triggers the final MoviePy compositing step for that section of the video.

Quick Previews
--------------

During quick-preview renders, you can bypass all compositing by setting
the ``SKIP_VIDEO_OVERLAY`` environment variable::

   SKIP_VIDEO_OVERLAY=True manim -pql my_scene.py MyScene

This will result in a partial movie file with blank rectangles where the videos should be (provided the :class:`~manim_videos.mobjects.VideoMObject` was added to the scene).
