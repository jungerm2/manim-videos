<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://jungerm2.github.io/manim-videos/latest/_static/logo_dark.svg">
    <img alt="manim-videos logo" src="https://jungerm2.github.io/manim-videos/latest/_static/logo_light.svg" width="500">
  </picture>
</p>

# Manim Videos

Efficiently embed video clips in **Manim** scenes and **Manim Slides** presentations.

Instead of decoding video frames one-by-one into `ImageMobject`s, `manim_videos`
renders a transparent placeholder during Manim's normal pass and then uses
[MoviePy](https://zulko.github.io/moviepy/) to composite the target video onto the
rendered partial movie file in a single post-processing step.

Note: This package is only tested against [Manim Community Edition](https://github.com/ManimCommunity/manim), but may work with [ManimGL](https://3b1b.github.io/manim/).

## Quick Start

Install manim-videos with:
```bash
pip install manim-videos
```

Then add the ``VideoMixin`` to your scene class, and add your video to your scene using the ``VideoMObject`` class and ``OverlayVideo`` animation:

```python
from manim import *
from manim_videos import VideoMixin, VideoMObject, OverlayVideo


class MyScene(VideoMixin, Scene):
    def construct(self):
        vid = VideoMObject("my_video.mp4")
        self.play(OverlayVideo(vid))
```

Which can be rendered and previewed using the following command:

```bash
manim -pql my_scene.py MyScene
```

See the [documentation](https://jungerm2.github.io/manim-videos/) for more!
