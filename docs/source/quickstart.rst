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
