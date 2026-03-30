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


class TrailerSlow(VideoMixin, Scene):
    def play_video(self, clip, scale=1.0, shift=ORIGIN):
        for frame in clip.iter_frames():
            im = ImageMobject(frame).scale_to_fit_height(2).scale(scale).shift(shift)
            self.add(im)
            self.wait(1 / clip.fps)
            self.remove(im)

    def construct(self) -> None:
        # Load the clip, adjust path or subclip as needed
        clip_path = "assets/big_buck_bunny_720p_h264.mov"
        clip = VideoFileClip(clip_path).without_audio()
        previous_clip = clip.subclipped((1, 14), (1, 19))
        next_clip = clip.subclipped((4, 42), (4, 44))
        prev_last_frame = (
            ImageMobject(previous_clip.get_frame(previous_clip.duration))
            .scale_to_fit_height(2)
            .scale(2.5)
            .shift(DOWN * 0.5)
        )
        next_last_frame = (
            ImageMobject(next_clip.get_frame(next_clip.duration)).scale_to_fit_height(2).scale(2.5).shift(DOWN * 0.5)
        )

        # Add some text for the trailer
        prev_text = Text("Previously on Big Buck Bunny...")
        next_text = Text("Stay tuned for more!").to_edge(UP)
        self.play(Write(prev_text))
        self.play(prev_text.animate.to_edge(UP))

        # The OverlayVideo animation will composite the video clip at render time.
        # It should be in it's own section.
        self.next_section()
        self.add(prev_last_frame)
        self.play_video(previous_clip, scale=2.5, shift=DOWN * 0.5)
        self.next_section()
        self.play(FadeOut(prev_last_frame))

        # Other animations can be included in the same section,
        # but they might be covered up by the video!
        self.next_section()
        self.play(ReplacementTransform(prev_text, next_text))
        self.play_video(next_clip, scale=2.5, shift=DOWN * 0.5)

        self.next_section()
        self.add(next_last_frame)
        self.play(FadeOut(next_last_frame))
