import pytest
from manim import LEFT, RIGHT
from moviepy import VideoFileClip

from manim_videos import OverlayVideo, VideoMObject

__module_test__ = "overlays"


def section_duration(section):
    return sum(
        VideoFileClip(partial_movie_file).duration for partial_movie_file in section.get_clean_partial_movie_files()
    )


@pytest.snapshot_frames_comparison(last_frame=False)
def test_basic_overlay(scene):
    video = VideoMObject(pytest.get_test_clip(num_images=15, fps=15)).stretch_to_keep_aspect()
    scene.play(OverlayVideo(video.scale(2.5)))


@pytest.snapshot_frames_comparison(last_frame=True)
def test_get_frame_position(scene):
    video = VideoMObject(pytest.get_test_clip(num_images=5, fps=5)).stretch_to_keep_aspect().scale(2.5)

    if pytest.snapshot_update:
        scene.add(video.get_last_frame())
        scene.wait()
    else:
        scene.play(OverlayVideo(video))


@pytest.snapshot_frames_comparison(last_frame=False)
def test_overlay_with_different_fps(scene):
    video1 = VideoMObject(pytest.get_test_clip(num_images=10, fps=30))
    video2 = VideoMObject(pytest.get_test_clip(num_images=50, fps=150))
    video3 = VideoMObject(pytest.get_test_clip(num_images=5, fps=15))
    video4 = VideoMObject(pytest.get_test_clip(num_images=9, fps=3))
    video1.next_to(video2, LEFT)
    video3.next_to(video2, RIGHT)
    scene.play(OverlayVideo(video1))
    scene.next_section()
    scene.play(OverlayVideo(video2))
    scene.next_section()
    scene.play(OverlayVideo(video3))
    scene.next_section()
    scene.play(OverlayVideo(video4.scale(2)))

    assert len(scene.renderer.file_writer.sections) == 4
    d1, d2, d3, d4 = [section_duration(section) for section in scene.renderer.file_writer.sections]
    assert d1 == d2 == d3 == 0.33
    assert d4 == 3.0


