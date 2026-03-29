from manim import *
from manim_slides import Slide
from moviepy import VideoFileClip, vfx

from manim_videos import OverlayVideo, VideoMixin, VideoMObject


class VideoSlide(VideoMixin, Slide):
    """Demonstrates VideoMObject inside a Manim Slides presentation."""

    skip_reversing = True

    def construct(self) -> None:
        text = Text("Video Demo!", color=GRAY)
        self.play(Write(text))

        # Load the clip, adjust path or subclip as needed
        clip = VideoFileClip("assets/big_buck_bunny_720p_h264.mov")

        # Select the subclip, loop it twice, and remove the audio
        # Moviepy can do a lot, see: https://zulko.github.io/moviepy/getting_started/moviepy_10_minutes.html#moviepy-10-minutes
        clip = clip.subclipped(10, 15).with_effects([vfx.Loop(2)]).without_audio()

        # Fade in the video, fade out the text
        self.next_slide(auto_next=True)
        vid = VideoMObject(clip).scale(3)
        vid_start = vid.get_first_frame()
        self.play(FadeOut(text), FadeIn(vid_start))

        # Play the video and loop the slide!
        # Again, note the section break (next slide) before and after playing the video,
        # here the section is automatically ended because it's the end of the slide deck.
        self.next_slide(loop=True)
        self.remove(vid_start)
        self.play(OverlayVideo(vid))
