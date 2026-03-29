from manim import *
from moviepy import VideoFileClip

from manim_videos import OverlayVideo, VideoMixin, VideoMObject


class VideoExample(VideoMixin, Scene):
    """Demonstrates VideoMObject inside a plain Manim scene."""

    def construct(self) -> None:
        # A simple shape to show before and after the video
        rec = Rectangle(height=1, width=1)
        self.play(Create(rec))
        self.wait()

        # Load the clip, adjust path or subclip as needed
        clip_path = "assets/big_buck_bunny_720p_h264.mov"
        clip = VideoFileClip(clip_path).subclipped(10, 15).without_audio()

        vid = VideoMObject(clip).scale(3.0)
        vid_start = vid.get_first_frame()
        vid_stop = vid.get_last_frame()

        # Show the first frame as a static image
        self.play(FadeIn(vid_start))
        self.remove(vid_start)

        # Play the video (composited at render time)
        # Note that there needs to be a section break before and after playing the video!
        self.next_section()
        self.play(OverlayVideo(vid))
        self.next_section()

        # Show the last frame
        self.play(FadeOut(vid_stop))

        # Resume normal Manim animations
        # Notice that the rectangel is still there, just under the overlayed video.
        self.play(Uncreate(rec))
        self.wait()
