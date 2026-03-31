from __future__ import annotations

import functools
import inspect
from pathlib import Path

import cairo
import imageio.v3 as iio
import moderngl
import numpy as np
import pytest
from manim import Scene, tempconfig
from moviepy import DataVideoClip, VideoFileClip
from syrupy.extensions.image import PNGImageSnapshotExtension
from syrupy.extensions.single_file import SingleFileSnapshotExtension

from manim_videos import VideoMixin


def pytest_report_header(config):
    try:
        ctx = moderngl.create_standalone_context()
        info = ctx.info
        ctx.release()
    except Exception as e:
        raise Exception("Error while creating moderngl context") from e

    return (
        f"\nCairo Version: {cairo.cairo_version()}",
        "\nOpenGL information",
        "------------------",
        f"vendor: {info['GL_VENDOR'].strip()}",
        f"renderer: {info['GL_RENDERER'].strip()}",
        f"version: {info['GL_VERSION'].strip()}\n",
    )


class VideoScene(VideoMixin, Scene):
    def construct(self):
        # Needed otherwise the test will fail because the video is not rendered
        self.renderer.skip_animations = False
        self.renderer.write_to_movie = True
        super().construct()


def get_test_clip(shape: tuple[int, int] = (128, 128), num_images: int = 150, fps: int = 30) -> DataVideoClip:
    """Create and return a synthetic test video clip, with a white circle moving from left to right (taken from mediapy)"""

    def generate_image(image_index: int) -> np.ndarray:
        """Returns a video frame image."""
        yx = np.moveaxis(np.indices(shape), 0, -1)
        image = (np.insert((yx + 0.5) / shape, 2, 0.0, axis=-1) * 255).astype(np.uint8)
        height, width = shape
        center = height * 0.6, width * (image_index + 0.5) / num_images
        radius_squared = (min(shape) * 0.1) ** 2
        inside = np.sum((yx - center) ** 2, axis=-1) < radius_squared
        image[inside] = 255, 255, 255
        return image

    clip = DataVideoClip(range(num_images), generate_image, fps)
    clip.filename = f"test_clip_{shape[0]}x{shape[1]}_{num_images}frames_{fps}fps"
    return clip


class ImageSnapshotExtension(PNGImageSnapshotExtension):
    """Syrupy extension for comparing images."""

    def serialize(self, data, **kwargs):
        """
        Hijack serialize to load the image data from the path.

        This works because the default snapshot writer will save the serialized data
        as a snapshot, and this serialized data was read from a valid image file.
        """
        with open(data, "rb") as f:
            return f.read()

    def matches(self, *, serialized_data, snapshot_data) -> bool:
        serialized_im = iio.imread(serialized_data)
        snapshot_im = iio.imread(snapshot_data)
        return np.allclose(serialized_im, snapshot_im)


class VideoSnapshotExtension(SingleFileSnapshotExtension):
    """Syrupy extension for comparing videos frame by frame."""

    file_extension = "mp4"

    def read_snapshot_data_from_location(
        self, *, snapshot_location: str, snapshot_name: str, session_id: str
    ) -> VideoFileClip | None:
        try:
            return self.serialize(snapshot_location)
        except FileNotFoundError:
            return None

    def serialize(self, path, **kwargs):
        """Hijack serialize to load the video file from the path."""
        return VideoFileClip(str(path))

    @classmethod
    def write_snapshot_collection(cls, *, snapshot_collection) -> None:
        filepath, data = (
            snapshot_collection.location,
            next(iter(snapshot_collection)).data,
        )
        data.write_videofile(filepath)

    def matches(self, *, serialized_data, snapshot_data) -> bool:
        if serialized_data.duration != snapshot_data.duration or serialized_data.fps != snapshot_data.fps:
            return False

        diff_frames = []
        is_match = True

        for frame_ser, frame_snp in zip(serialized_data.iter_frames(), snapshot_data.iter_frames(), strict=True):
            diff = np.abs(frame_ser.astype(np.int16) - frame_snp.astype(np.int16))
            diff_frames.append(diff.astype(np.uint8))
            is_match = is_match and diff.mean() < 1

            if not pytest.video_debug_enabled and not is_match:
                break

        if not is_match:
            diff_path = Path(serialized_data.filename).parent / "diff.png"
            iio.imwrite(diff_path, diff_frames[-1])

            if pytest.video_debug_enabled:
                diff_path = Path(serialized_data.filename).parent / "diff.mp4"
                clip = DataVideoClip(diff_frames, lambda frame: frame, fps=serialized_data.fps)
                clip.write_videofile(str(diff_path), logger=None)
                clip.close()

        return is_match


def snapshot_frames_comparison(*, last_frame=False, base_scene=VideoScene, quality="low_quality"):
    """
    Similar to manim's `frames_comparison` but this actually renders to scene
    to a tempdir out to a physical .mp4 file which enables moviepy to be used
    to composite the video. Then frames are extracted as PNGs and snapshot
    testing is performed with Syrupy.
    """

    def decorator_maker(tested_scene_construct):
        @functools.wraps(tested_scene_construct)
        def wrapper(*args, snapshot, tmp_path, **kwargs):
            config_overrides = {
                "media_dir": str(tmp_path),
                "write_to_movie": True,
                "format": "mp4",
                "quality": quality,
                "dry_run": False,
                "disable_caching": True,
                "verbosity": "WARNING",
            }

            with tempconfig(config_overrides):

                class TestedScene(base_scene):
                    def construct(self):
                        tested_scene_construct(self, *args, **kwargs)

                scene = TestedScene()
                scene.render()

                mp4_files = list(tmp_path.rglob(f"{scene.__class__.__name__}.mp4"))
                assert len(mp4_files) == 1, "No .mp4 file was generated"
                mp4_path = mp4_files[0]

                if last_frame:
                    clip = VideoFileClip(str(mp4_path))
                    frame = clip.get_frame(clip.duration - 1 / clip.fps)
                    frame_path = tmp_path / "last.png"
                    iio.imwrite(frame_path, frame)
                    clip.close()

                    assert frame_path == snapshot(extension_class=ImageSnapshotExtension, name="last"), (
                        "Generated preview does not match the reference snapshot"
                    )
                else:
                    assert mp4_path == snapshot(extension_class=VideoSnapshotExtension), (
                        "Generated video does not match the reference snapshot"
                    )

        sig = inspect.signature(tested_scene_construct)
        params = [p for p in sig.parameters.values() if p.name != "scene"]
        if not any(p.name == "snapshot" for p in params):
            params.append(inspect.Parameter("snapshot", inspect.Parameter.KEYWORD_ONLY))
        if not any(p.name == "tmp_path" for p in params):
            params.append(inspect.Parameter("tmp_path", inspect.Parameter.KEYWORD_ONLY))
        wrapper.__signature__ = sig.replace(parameters=params)
        return wrapper

    return decorator_maker


def pytest_addoption(parser):
    parser.addoption("--video-debug", action="store_true", default=False, help="Enable debug mode for video snapshots")


def pytest_configure(config):
    """
    Add the helper functions to the pytest namespace since we cannot
    simply import them from a utils module because of the way pytest
    discovers and runs tests.
    """
    pytest.snapshot_frames_comparison = snapshot_frames_comparison
    pytest.get_test_clip = get_test_clip
    pytest.VideoScene = VideoScene
    pytest.video_debug_enabled = config.getoption("--video-debug")
