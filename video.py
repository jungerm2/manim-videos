import os
import warnings
from ast import literal_eval
from functools import partial
from pathlib import Path

from manim import *
from manim.utils.parameter_parsing import flatten_iterable_parameters
from moviepy import *
from manim_slides import Slide


class OverlayVideo(Wait):
    def __init__(self, video_mobject, *args, **kwargs):
        self.video_mobject = video_mobject
        self.section_paths = []
        self.skip_animations = False
        super().__init__(*args, **kwargs)

    @staticmethod
    def coords_to_pix(scene, point):
        # Note: The coordinate system of moviepy is origin at top left corner, so invert X-axis
        conversion = np.array(
            [
                scene.renderer.camera.pixel_width / scene.renderer.camera.frame_width,
                -scene.renderer.camera.pixel_height / scene.renderer.camera.frame_height,
                1,
            ]
        )
        offset = np.array([scene.renderer.camera.pixel_width / 2, scene.renderer.camera.pixel_height / 2, 0])
        return (np.array(point) - scene.renderer.camera.frame_center) * conversion + offset

    def clean_up_from_scene(self, scene: Scene) -> None:
        # Don't actually do any clean up, just use it as a hook to get access to the scene object
        super().clean_up_from_scene(scene)
        self.section_paths = scene.renderer.file_writer.sections[-1].partial_movie_files

        # If skip_animations was set (either because this partial movie was cached, or was explicitly
        # skipped by the user) we also skip `finalize` and do not overlay the video.
        self.skip_animations = scene.renderer.skip_animations

        # Calculate pixel coordinates while we have access to the scene
        right = self.coords_to_pix(scene, self.video_mobject.get_right())
        left = self.coords_to_pix(scene, self.video_mobject.get_left())
        top = self.coords_to_pix(scene, self.video_mobject.get_top())
        btm = self.coords_to_pix(scene, self.video_mobject.get_bottom())
        self.upper_left = self.coords_to_pix(scene, self.video_mobject.get_boundary_point(UL))[:-1]
        self.width = abs(right - left)[0]
        self.height = abs(top - btm)[1]

    def finalize(self):
        if not self.skip_animations:
            if len(self.section_paths) > 1:
                # Filter out all clips that are too short/long
                duration = self.video_mobject.get_clip().duration
                self.section_paths = [
                    p for p in self.section_paths if np.allclose(VideoFileClip(p).duration, duration, rtol=0.05)
                ]
                warnings.warn(
                    "Found more than one partial movie file, selecting the one with similar duration as expected.",
                    RuntimeWarning,
                )
            if not self.section_paths:
                raise RuntimeError(
                    f"Exactly one partial movie file is needed to overlay video on, instead got {self.section_paths}. "
                    "Try adding `self.next_section()` before and after the play call."
                )

            # Overlay the text clip on the first video clip
            section_video = VideoFileClip(self.section_paths[0])
            clip = (
                self.video_mobject.get_clip()
                .resized((self.width, self.height))
                .with_position(tuple(self.upper_left))
                .with_fps(int(config["frame_rate"]))
            )
            video = CompositeVideoClip([section_video, clip])

            # Write the result to the original section file
            # Due to a bug, write to a temp file and replace original, see: https://github.com/Zulko/moviepy/issues/1029
            path = (
                Path(self.section_paths[0])
                .with_name("temporary_overlay")
                .with_suffix(Path(self.section_paths[0]).suffix)
            )
            video.write_videofile(str(path))
            os.replace(str(path), self.section_paths[0])


class VideoMObject(Rectangle):
    """Enables Videos to be overlayed on top of scene.
    Works by intercepting when the current partial movie file is done rendering and will override
    it with the video being composited in.

    Alternative to # https://github.com/3b1b/manim/issues/760
    """

    def __init__(self, clip, *args, stroke_width=0, fill_color=GRAY, fill_opacity=1.0, **kwargs):
        super().__init__(*args, stroke_width=stroke_width, fill_color=fill_color, fill_opacity=fill_opacity, **kwargs)

        # IMPORTANT: Here we capture a reference to the clip object via a closure, this enables us to access
        #   the clip by calling `get_clip` yet does not directly put the clip in the `__dict__` attribute.
        #   Manim hashes objects by hashing their `__dict__`'s recursively and `clip.reader.proc` is a
        #   subprocess to FFMPEG which contains attributes like the PID which are randomly generated.
        #   If not careful and these are allowed to be hashed, then two identical clips will have different hashes.
        # On the other hand: Currying the clip like below means that the actual clip contents are not hashed, only
        #   it's "manin-style" attributes such as size, position, and clip filename since it's added to self via
        #   self.text below. For instance if you render a VideoMObject of a subclip (0-1) and change it to (1-2)
        #   it will think it was already cached! Other attrs might cause similar issues...
        if isinstance(clip, (str, Path)):
            clip = VideoFileClip(clip)
        self.get_clip = partial(lambda: clip)

        self.text = Text(f"Video clip of:\n{clip.filename}", color="black").move_to(self.get_center())
        self.text.scale_to_fit_width(self.width * 0.95)
        self.add(self.text)

    def stretch_to_keep_aspect(self, keep_dim=0):
        h, w = self.get_clip().h, self.get_clip().w
        self.remove(self.text)

        if keep_dim == 0:
            self.stretch_to_fit_height(self.width * h / w)
        elif keep_dim == 1:
            self.stretch_to_fit_width(self.height * w / h)
        else:
            raise ValueError(f"Argument `keep_dim` can only be 0 (width) or 1 (height), got {keep_dim}.")

        self.text.scale_to_fit_width(self.width * 0.95)
        self.add(self.text)
        return self

    def _get_border(self):
        return (
            Rectangle()
            .stretch_to_fit_width(self.width)
            .stretch_to_fit_height(self.height)
            .move_to(self.get_center())
            .set_stroke(self.stroke_color, self.stroke_opacity)
        )

    def get_frame(self, t):
        """Return desired frame as an ImageMObject overlayed on top of the video's border"""
        return Group(
            self._get_border(),
            ImageMobject(self.get_clip().get_frame(t=t))
            .stretch_to_fit_width(self.width)
            .stretch_to_fit_height(self.height)
            .move_to(self.get_center()),
        )

    def get_first_frame(self):
        return self.get_frame(0)

    def get_last_frame(self):
        return self.get_frame(self.get_clip().end - 1 / self.get_clip().fps)

    def play(self):
        anim = OverlayVideo(
            video_mobject=self,
            run_time=self.get_clip().duration,
            frozen_frame=False,
        )
        return anim


class VideoMixin:
    def play(self, *args, **kwargs):
        """Same as Scene.play but will call any remaining finalize methods to overlay videos

        Note: This is not very efficient as it will overlay one video at a time, but it's still
            wildly more efficient than displaying videos one frame at a time using ImageMObjects.
        """
        if not literal_eval(os.environ.get("SKIP_VIDEO_OVERLAY", "False")):
            overlays = filter(lambda a: isinstance(a, OverlayVideo), flatten_iterable_parameters(args))
            overlays = sorted(overlays, key=lambda a: a.video_mobject.z_index)

            for anim in overlays:
                anim.video_mobject.set_fill(opacity=0.0, color=config.background_color)
                anim.video_mobject.set_stroke(opacity=0.0, color=config.background_color)

            super().play(*args, **kwargs)

            for anim in overlays:
                anim.finalize()
        else:
            super().play(*args, **kwargs)


class VideoExample(VideoMixin, Scene):
    def construct(self):
        rec = Rectangle(
            height=1,
            width=1,
        )
        self.play(Create(rec))
        self.wait()
        self.remove(rec)

        # Load big_buck_bunny and select the subclip
        # wget https://archive.org/download/BigBuckBunny/big_buck_bunny_720p_h264.mov
        clip_path = "assets/big_buck_bunny_720p_h264.mov"
        clip = VideoFileClip(clip_path).subclipped(10, 15).without_audio()
        vid = VideoMObject(clip)
        vid_start = vid.get_first_frame()
        vid_stop = vid.get_last_frame()

        self.add(vid_start)
        self.wait()
        self.remove(vid_start)

        self.next_section()
        self.add(vid)
        self.play(vid.play())
        self.next_section()

        self.add(vid_stop)
        self.wait()
        self.remove(vid_stop)

        rec = Rectangle(
            height=1,
            width=1,
        )
        self.add(rec)
        self.wait()
        self.remove(rec)


class VideoSlide(VideoMixin, Slide):
    def construct(self):
        text = Text("Video Demo!", color=GRAY)
        self.play(Write(text))
        self.next_slide(auto_next=True)
        
        # Load big_buck_bunny and select the subclip
        # wget https://archive.org/download/BigBuckBunny/big_buck_bunny_720p_h264.mov
        clip_path = "assets/big_buck_bunny_720p_h264.mov"
        clip = VideoFileClip(clip_path).subclipped(10, 15).with_effect([vfx.Loop(30)]).without_audio()
        vid = VideoMObject(clip).scale(3)
        vid_start = vid.get_first_frame()
        self.play(FadeOut(text), FadeIn(vid_start))

        self.next_slide(loop=True)
        self.remove(vid_start)
        self.play(vid.play())
