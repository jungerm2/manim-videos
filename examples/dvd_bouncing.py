import itertools
import requests
from pathlib import Path

import numpy as np
from manim import *
from manim.utils import rate_functions
from PIL import Image
from moviepy import DataVideoClip, VideoClip, VideoFileClip, vfx
from moviepy.video.tools.drawing import color_gradient

from manim_videos import VideoMObject, OverlayVideo, VideoMixin


LOGO_PATH = "assets/DVD_VIDEO_logo.png"
GRADIENT_PATH = "assets/gradients-{num_frames}.mp4"
LOGO_URL = "https://upload.wikimedia.org/wikipedia/commons/6/64/DVD_VIDEO_logo.png"
COLORS = ["#be00ff", "#00feff", "#ff8300", "#0026ff", "#fffa01", "#ff2600", "#ff008b", "#be00ff", "#00feff"]
COLORS = [tuple(bytes.fromhex(hex_color.strip("#"))) for hex_color in COLORS]


class DVDBouncing(VideoMixin, Scene):
    @staticmethod
    def make_dvd_logo_video(num_frames=120, fps=30):
        if not Path(LOGO_PATH).exists():
            mask_im = Image.open(requests.get(LOGO_URL, stream=True).content)
            mask_im.save(LOGO_PATH)

        mask_im = Image.open(LOGO_PATH)
        mask_arr = np.array(mask_im).astype(np.float64)[..., -1] / 255
        mask = VideoClip(is_mask=True, frame_function=lambda t: mask_arr)

        if Path(GRADIENT_PATH.format(num_frames=num_frames)).exists():
            return VideoFileClip(str(Path(GRADIENT_PATH.format(num_frames=num_frames)))).with_mask(mask).with_fps(fps)

        color_ramp = np.zeros((mask.h, (len(COLORS) - 1) * mask.w, 3), dtype=np.uint8)

        for i, (c1, c2) in enumerate(itertools.pairwise(COLORS)):
            color_ramp[:, i * mask.w : (i + 1) * mask.w, :3] = color_gradient(
                (mask.w, mask.h), p1=(0, mask.h / 2), p2=(mask.w, mask.h / 2), color_1=c2, color_2=c1, shape="bilinear"
            )

        Image.fromarray(color_ramp).show()

        clip = (
            DataVideoClip(
                np.linspace(0, mask.w * (len(COLORS) - 2), num_frames),
                lambda i: color_ramp[:, int(i) : int(i) + mask.w],
                fps=fps,
            )
            .with_fps(fps)
            .with_mask(mask)
        )

        clip.write_videofile(str(Path(GRADIENT_PATH.format(num_frames=num_frames))))
        return clip

    def construct(self):
        # Get DVD logo video and spin in into action!
        clip = self.make_dvd_logo_video().with_effects([vfx.Loop(2)])
        video = VideoMObject(clip).stretch_to_keep_aspect().scale(1.5)
        self.play(OverlayVideo(video), SpinInFromNothing(video, angle=6 * PI, run_time=video.duration / 2))
        self.next_section()

        # Shrink logo to prepare for the bouncing animation
        height, width = video.height, video.width
        self.play(
            OverlayVideo(video),
            Succession(
                ApplyMethod(
                    video.stretch_to_fit_width,
                    width * 0.5,
                    rate_func=rate_functions.ease_out_elastic,
                    run_time=video.duration / 3,
                ),
                ApplyMethod(
                    video.stretch_to_fit_height,
                    height * 0.5,
                    rate_func=rate_functions.ease_out_elastic,
                    run_time=video.duration / 3,
                ),
            ),
        )
        self.next_section()

        # Collision detection, just mirroring the velocity vector
        def bounce_updater(m, dt):
            m.shift(m.velocity * dt)

            w, h = m.width / 2, m.height / 2
            fw, fh = config.frame_width / 2, config.frame_height / 2

            if abs(m.get_x()) + w > fw:
                m.velocity[0] *= -1
                m.set_x(np.sign(m.get_x()) * (fw - w))

            if abs(m.get_y()) + h > fh:
                m.velocity[1] *= -1
                m.set_y(np.sign(m.get_y()) * (fh - h))

        # Add initial velocity and updater (which will move the video and handle collisions)
        self.add(video)
        video.velocity = DR
        video.add_updater(bounce_updater)

        # Play the animation for 5 times the duration of the video (which was already looped twice)
        for _ in range(4):
            self.play(OverlayVideo(video))
            self.next_section()
