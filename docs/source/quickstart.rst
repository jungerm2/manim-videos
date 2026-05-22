Quick Start
===========

Installation
------------

First, install ``manim-videos``:

.. code-block:: bash

   pip install manim-videos 


.. note::

   If using `manim-slides <https://eertmans.be/manim-slides/>`_, it must be installed
   separately, it is *not* bundled with ``manim-videos``.



Videos in a Manim Scene
-----------------------

To use ``manim-videos``, your scene should inherit from :class:`~manim_videos.VideoMixin` *before* the Manim base class (Scene or ThreeDScene, etc.), then you can use :class:`~manim_videos.VideoMObject` as a video object, which will be composited at render time using the :class:`~manim_videos.OverlayVideo`
animation:

.. manim:: Trailer

   from manim import *
   from moviepy import VideoFileClip

   from manim_videos import OverlayVideo, VideoMixin, VideoMObject


   class Trailer(VideoMixin, Scene):
      def construct(self) -> None:
         # Load the clip, adjust path or subclip as needed
         clip_path = "assets/big_buck_bunny_720p_h264.mov"
         clip = VideoFileClip(clip_path).without_audio()
         previous_clip = clip.subclipped((1, 14), (1, 19))
         next_clip = clip.subclipped((4, 42), (4, 44))
         prev_vid = VideoMObject(previous_clip).scale(2.5).shift(DOWN * 0.5)
         next_vid = VideoMObject(next_clip).scale(2.5).shift(DOWN * 0.5)
         prev_last_frame = prev_vid.get_last_frame()
         next_last_frame = next_vid.get_last_frame()

         # Add some text for the trailer
         prev_text = Text("Previously on Big Buck Bunny...")
         next_text = Text("Stay tuned for more!").to_edge(UP)
         self.play(Write(prev_text))
         self.next_section()
         self.play(prev_text.animate.to_edge(UP))

         # The OverlayVideo animation will composite the video clip at render time.
         # It should be in it's own section.
         self.next_section()
         self.add(prev_last_frame)
         self.play(OverlayVideo(prev_vid))
         self.next_section()
         self.play(FadeOut(prev_last_frame))

         # Other animations can be included in the same section,
         # but they might be covered up by the video!
         self.next_section()
         self.play(ReplacementTransform(prev_text, next_text), OverlayVideo(next_vid))

         self.next_section()
         self.add(next_last_frame)
         self.play(FadeOut(next_last_frame))


The above can be rendered with::

   manim -pql my_scene.py MyScene


Videos in a Manim Slides Presentation
---------------------------------------

Using ``manim-videos`` with manim-slides is very similar to using it with manim, but you must inherit from ``Slide`` (or ``ThreeDSlide``) instead of ``Scene``, and use ``self.next_slide()`` instead of ``self.next_section()``. Here's what the previous example looks like when used with manim-slides:

.. manim-slides:: TrailerSlide
   :hide_source:

   from manim import *
   from manim_slides import Slide
   from moviepy import VideoFileClip

   from manim_videos import OverlayVideo, VideoMixin, VideoMObject


   class TrailerSlide(VideoMixin, Slide):
      def construct(self) -> None:
         # Load the clip, adjust path or subclip as needed
         clip_path = "assets/big_buck_bunny_720p_h264.mov"
         clip = VideoFileClip(clip_path).without_audio()
         previous_clip = clip.subclipped((1, 14), (1, 19))
         next_clip = clip.subclipped((4, 42), (4, 44))
         prev_vid = VideoMObject(previous_clip).scale(2.5).shift(DOWN * 0.5)
         next_vid = VideoMObject(next_clip).scale(2.5).shift(DOWN * 0.5)
         prev_last_frame = prev_vid.get_last_frame()
         next_last_frame = next_vid.get_last_frame()

         # Add some text for the trailer
         prev_text = Text("Previously on Big Buck Bunny...")
         next_text = Text("Stay tuned for more!").to_edge(UP)
         self.play(Write(prev_text))
         self.next_slide()
         self.play(prev_text.animate.to_edge(UP))

         # The OverlayVideo animation will composite the video clip at render time.
         # It should be in it's own section.
         self.next_slide()
         self.add(prev_last_frame)
         self.play(OverlayVideo(prev_vid))
         self.next_slide()
         self.play(FadeOut(prev_last_frame))

         # Other animations can be included in the same section,
         # but they might be covered up by the video!
         self.next_slide()
         self.play(ReplacementTransform(prev_text, next_text), OverlayVideo(next_vid))

         self.next_slide()
         self.add(next_last_frame)
         self.play(FadeOut(next_last_frame))


Render and present using::

   manim-slides render my_scene.py MySlide
   manim-slides present MySlide


.. tip::

   You can use ``auto_next=True`` in ``next_slide()`` to automatically advance to the next slide after the current animations finish which can help with transitions.


Animated Effects
----------------

Movement and Transformations (Shift, Scale, Rotate)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Because ``OverlayVideo`` dynamically computes a (perspective transform) homography matrix from the four corners of the ``VideoMObject`` at each frame, you can apply any standard Manim positioning, scaling, or rotation animation to the video object. The video overlay will warp and move seamlessly with the placeholder.

This supports:
* **Shifting / Moving** (e.g., using ``.animate.shift(...)`` or updater-driven movement).
* **Scaling** (e.g., using ``.animate.scale(...)``).
* **Rotation** (e.g., using ``Rotate(...)`` or ``.animate.rotate(...)``).

For example, to scale, rotate, and shift a video simultaneously:

.. manim:: MoveAndTransformExample

    from manim import *
    from moviepy import VideoFileClip
    from manim_videos import OverlayVideo, VideoMixin, VideoMObject

    class MoveAndTransformExample(VideoMixin, Scene):
        def construct(self) -> None:
            clip = VideoFileClip("assets/rickroll.mp4").without_audio()
            vid = (
                VideoMObject(clip)
                .stretch_to_keep_aspect()
                .shift(LEFT * 2)
            )
            self.add(vid)
            self.play(
                OverlayVideo(vid),
                vid.animate(run_time=5).scale(2).rotate(PI / 2).shift(RIGHT * 4)
            )

Alternatively, you can use a specific animation class like ``Rotate``.

.. note::

   Manim-videos doesn't support audio at the moment due to manim limitations.


Fade In / Fade Out
~~~~~~~~~~~~~~~~~~

:class:`~manim.FadeIn` and :class:`~manim.FadeOut` work transparently with
:class:`~manim_videos.OverlayVideo` when run in the **same** ``play()`` call.
The per-frame opacity of the :class:`~manim_videos.VideoMObject` is sampled
during the animation and applied as a uniform alpha multiplier to the
composited clip:

.. manim:: FadeExample

    from manim import *
    from moviepy import VideoFileClip
    from manim_videos import OverlayVideo, VideoMixin, VideoMObject

    class FadeExample(VideoMixin, Scene):
        def construct(self) -> None:
            clip = VideoFileClip("assets/rickroll.mp4").without_audio()
            vid = (
                VideoMObject(clip)
                .scale(3.0)
                .stretch_to_keep_aspect()
            )
            self.play(
                Succession(
                    FadeIn(vid, run_time=1.0),
                    Wait(run_time=clip.duration-2),
                    FadeOut(vid, run_time=1.0)
                ),
                OverlayVideo(vid)
            )

.. note::

    Opacity is tracked via the mobject's ``stroke_opacity``.  Because
    :class:`~manim_videos.VideoMObject` uses ``fill_opacity=0`` (it is a
    transparent placeholder), fade animations must target the whole mobject
    (not just its fill) for the effect to be picked up by
    :class:`~manim_videos.OverlayVideo`. Standard
    :class:`~manim.FadeIn` / :class:`~manim.FadeOut` satisfy this requirement
    automatically.


Rounded Corners
~~~~~~~~~~~~~~~

Call :meth:`~manim_videos.VideoMObject.round_corners` on a
:class:`~manim_videos.VideoMObject` to clip the composited video to a rounded
rectangle. The radius is specified in **Manim scene units** and is applied
during the compositing pass:

.. manim:: StaticRoundedCornersExample

    from manim import *
    from moviepy import VideoFileClip
    from manim_videos import OverlayVideo, VideoMixin, VideoMObject

    class StaticRoundedCornersExample(VideoMixin, Scene):
        def construct(self) -> None:
            clip = VideoFileClip("assets/thatsallfolks.mp4").without_audio()
            vid = (
                VideoMObject(clip).scale(2.0)
                .stretch_to_keep_aspect()
            )
            vid.round_corners(radius=0.4)
            self.play(OverlayVideo(vid))

The radius can also be **animated** using ``always_redraw`` together with a
:class:`~manim.ValueTracker`, so the corners change smoothly over time:

.. manim:: AnimatedRoundedCornersExample

    from manim import *
    from moviepy import VideoFileClip
    from manim_videos import OverlayVideo, VideoMixin, VideoMObject

    class AnimatedRoundedCornersExample(VideoMixin, Scene):
        def construct(self) -> None:
            clip = VideoFileClip("assets/thatsallfolks.mp4").without_audio()
            radius = ValueTracker(0.0)
            vid = always_redraw(
                lambda: (
                    VideoMObject(clip)
                    .scale(2.0)
                    .stretch_to_keep_aspect()
                    .round_corners(radius.get_value())
                )
            )
            self.add(vid)
            self.play(OverlayVideo(vid), radius.animate(run_time=3.0).set_value(2.0))


Full Example: DVD Bouncing Logo
-------------------------------

To tie everything together, here's a modern take on a classic animation with an animated video logo (taken from the `examples directory <https://github.com/jungerm2/manim-videos/tree/main/examples>`_):

.. manim:: DVDBouncing
   :hide_source:

   from examples.dvd_bouncing import DVDBouncing
