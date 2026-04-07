import numpy as np
import pytest
from manim import BLUE, DEGREES, DOWN, LEFT, ORIGIN, PI, RIGHT, UP, FadeIn, Rotate, Text, ValueTracker, always_redraw
from manim.utils import rate_functions
from moviepy import VideoFileClip

from manim_videos import OverlayVideo, VideoMObject

__module_test__ = "overlays"


def section_duration(section):
    return sum(
        VideoFileClip(partial_movie_file).duration for partial_movie_file in section.get_clean_partial_movie_files()
    )


@pytest.snapshot_frames_comparison(last_frame=False)
def test_basic_overlay(scene):
    video = VideoMObject(pytest.get_test_clip(num_images=15, fps=15)).stretch_to_keep_aspect().scale(1.5)
    outline = video.get_border().set_stroke(color=BLUE, width=5)
    scene.add(outline)
    scene.play(OverlayVideo(video))


@pytest.snapshot_frames_comparison(last_frame=False)
def test_basic_overlay_with_mask(scene):
    video = VideoMObject(pytest.get_test_clip(num_images=15, fps=15, mask=True)).stretch_to_keep_aspect().scale(1.5)
    outline = video.get_border().set_stroke(color=BLUE, width=5)
    scene.add(outline)
    scene.play(OverlayVideo(video))


def test_ordered_vertices():
    video = VideoMObject(pytest.get_test_clip(num_images=1, fps=15))
    vertices = video.get_ordered_vertices()
    video.reverse_direction()
    vertices_rev = video.get_ordered_vertices()
    assert np.allclose(vertices, vertices_rev)


@pytest.mark.parametrize(
    "size, shift, rotate, mask, t",
    [
        ((1, 1), ORIGIN, 0, False, 0),
        ((2, 2), UP, 90, False, 0.5 - 1 / 10),
        ((3, 4), DOWN, 180, False, 1 - 1 / 5),
        ((1, 1), ORIGIN, 0, True, 0),
        ((2, 2), UP, 90, True, 0.5 - 1 / 10),
        ((3, 4), DOWN, 180, True, 1 - 1 / 5),
    ],
)
@pytest.snapshot_frames_comparison(last_frame=True)
def test_get_frame(scene, size, shift, rotate, mask, t):
    height, width = size
    video = VideoMObject(pytest.get_test_clip(num_images=5, fps=5, mask=mask))
    video = video.stretch_to_fit_height(height).stretch_to_fit_width(width)
    video = video.shift(shift).rotate(rotate * DEGREES)

    if pytest.snapshot_update:
        scene.add(video.get_frame(t))
        scene.wait()
    else:
        scene.play(OverlayVideo(video))


@pytest.mark.parametrize(
    "size, shift, rotate",
    [
        ((1, 1), ORIGIN, 0),
        ((2, 2), UP, 90),
        ((3, 4), DOWN, 180),
    ],
)
def test_video_border(size, shift, rotate):
    height, width = size
    video = VideoMObject(pytest.get_test_clip(num_images=15, fps=15))
    video = video.stretch_to_fit_height(height).stretch_to_fit_width(width)
    video = video.shift(shift).rotate(rotate * DEGREES)
    border = video.get_border()
    assert border.width == video.width
    assert border.height == video.height
    assert border.stroke_width == video.stroke_width
    assert border.stroke_opacity == video.stroke_opacity
    assert border.stroke_color == video.stroke_color
    assert np.allclose(border.points, video.points)


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


@pytest.snapshot_frames_comparison(last_frame=False)
def test_shifted_overlay(scene):
    # Text ensures video alpha channel is properly rendered
    text1 = Text("Animated").rotate(90 * DEGREES).to_edge(LEFT)
    text2 = Text("Overlay").rotate(90 * DEGREES).to_edge(RIGHT)
    video = VideoMObject(pytest.get_test_clip(num_images=30, fps=15)).stretch_to_keep_aspect().scale(1.5)
    outline = video.get_border().set_stroke(color=BLUE, width=5)
    scene.play(
        OverlayVideo(video),
        video.animate(rate_func=rate_functions.wiggle, run_time=2).shift(LEFT * 3),
        outline.animate(rate_func=rate_functions.wiggle, run_time=2).shift(LEFT * 3),
        FadeIn(text1),
        FadeIn(text2),
    )


@pytest.snapshot_frames_comparison(last_frame=False)
def test_rotated_overlay(scene):
    # Note: We do not use `animate.rotate` here because it applies a transformation from the initial state
    # to the final rotated state (interpolation between the two states), without showing proper rotation
    # See: https://docs.manim.community/en/stable/reference/manim.mobject.mobject.Mobject.html#manim.mobject.mobject.Mobject.rotate
    video = VideoMObject(pytest.get_test_clip(num_images=15, fps=15)).stretch_to_keep_aspect().rotate(PI / 4)
    outline = video.get_border().set_stroke(color=BLUE, width=5).scale(1.025)
    scene.play(OverlayVideo(video), Rotate(video, angle=PI / 2), Rotate(outline, angle=PI / 2))


@pytest.snapshot_frames_comparison(last_frame=False)
def test_scaled_overlay(scene):
    video = VideoMObject(pytest.get_test_clip(num_images=15, fps=15)).stretch_to_keep_aspect().scale(0.5)
    outline = video.get_border().set_stroke(color=BLUE, width=5).scale(1.025)
    scene.play(
        OverlayVideo(video),
        video.animate.scale(2),
        outline.animate.scale(2),
    )


@pytest.snapshot_frames_comparison(last_frame=False)
def test_complex_overlay(scene):
    video = VideoMObject(pytest.get_test_clip(num_images=15, fps=15)).stretch_to_keep_aspect().scale(2)
    outline = video.get_border().set_stroke(color=BLUE, width=5)
    scene.play(
        OverlayVideo(video),
        video.animate.shift(RIGHT + UP).rotate(PI / 4).scale(0.5),
        outline.animate.shift(RIGHT + UP).rotate(PI / 4).scale(0.5),
    )


@pytest.snapshot_frames_comparison(last_frame=False)
def test_always_redraw_sync(scene):
    time = ValueTracker(0)
    clip = pytest.get_test_clip(num_images=30, fps=15, mask=True)

    video = always_redraw(
        lambda: VideoMObject(clip).stretch_to_keep_aspect().scale(1.5).shift(time.get_value() * RIGHT + 2 * LEFT)
    )
    outline = video.get_border().set_stroke(color=BLUE, width=5)
    scene.add(outline)
    scene.add(video)

    scene.play(OverlayVideo(video), time.animate(run_time=2).set_value(4), outline.animate(run_time=2).shift(4 * RIGHT))
