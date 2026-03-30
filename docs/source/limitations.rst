.. _limitations:

Limitations
===========

While ``manim-videos`` provides a highly efficient way to embed video into Manim, there are some important architectural limitations to keep in mind, primarily related to Manim's internal caching system and rendering pipeline.

.. _video-caching:

Video Caching
-------------

Manim determines whether an animation needs to be re-rendered by hashing the mobjects and parameters involved in a ``play()`` call. If the hash matches a previously rendered file, Manim skips the render pass and uses the cached file.

One way to extend this hash-based caching mechanism to ``manim-videos`` would be to hash the video file itself. However, the clip can be modified by moviepy (e.g. subclip, loop, etc.) and the hash of the original file would not match the hash of the modified clip. 

Thus, currently **Manim cannot know when the contents of the video file have changed.** If you modify your source video file but leave the :class:`~manim_videos.mobjects.VideoMObject`
properties (like width, height, or position) unchanged, Manim will likely
reuse the cached partial movie file, and the new video content will **not**
be overlayed.

To force a re-render when a video file changes, you can:

* Change a visual property of the :class:`~manim_videos.mobjects.VideoMObject` (e.g., a tiny change in scale or position).
* Clear the Manim cache manually (by deleting the relevant files in the ``media/videos/`` directory).
* Use the ``--disable_caching`` flag when running Manim.

Sectioning Requirement
----------------------

The :class:`~manim_videos.mixins.VideoMixin` relies on Manim's sectioning system to identify which partial movie files need to be processed. For the most reliable results, **every video animation should be isolated in its own section.**

Ideally, your code should look like this:

.. code-block:: python

    self.next_section()
    self.play(OverlayVideo(vid))
    self.next_section()

Failing to use ``next_section()`` properly can lead to a ``RuntimeError`` if the :class:`~manim_videos.mixins.VideoMixin` cannot uniquely identify which partial movie file corresponds to which video clip.

.. note::
    When using ``manim-slides``, you should still use ``next_section()`` to separate video animations from other content, this can also be done via ``self.next_slide()``.

Multiple Simultaneous Videos
----------------------------

You can play multiple videos at once in a single ``play()`` call, provided they have the same *exact* duration (since they will be composited onto the same partial movie file):

.. code-block:: python

    self.play(OverlayVideo(vid1), OverlayVideo(vid2))

However, this is inefficient as it will trigger two compositing passes on the same partial movie file (``partial_movie_file`` → ``partial_movie_file`` + ``vid1`` → ``partial_movie_file`` + ``vid1`` + ``vid2``).

A better approach is to use `moviepy's powerful video editing capabilities <https://zulko.github.io/moviepy/getting_started/moviepy_10_minutes.html#moviepy-10-minutes>`_ to composite the videos, and then play them as a single video clip:

.. code-block:: python

    from moviepy import VideoFileClip, clips_array

    clip1 = VideoFileClip("clip1.mp4")
    clip2 = VideoFileClip("clip2.mp4")
    combined_clip = clips_array([clip1, clip2])
    vid = VideoMObject(combined_clip)
    self.play(OverlayVideo(vid))
    
This is a more efficient way to play the clips side by side as it only triggers one compositing pass, however, clip positioning is now done via moviepy instead of Manim, which used pixel coordinates.

.. _z-order:

Z-Order and Layering
--------------------

Because the compositing pass happens **after** Manim has finished rendering a section, the video clip is always layered **on top** of all other mobjects in that same partial movie file.

If you have other Manim mobjects (like text, shapes, etc.) that overlap with the :class:`~manim_videos.mobjects.VideoMObject` in the same ``play()`` call, they will be covered up by the video clip in the final output, regardless of their Manim ``z_index``.

Multiple videos played in the same ``play()`` call are layered relative to each other according to their Manim ``z_index``, but the entire group will still appear on top of all non-video content in that section.
