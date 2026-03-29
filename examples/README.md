# Examples

This directory contains self-contained examples showing how to use `manim_videos`.

## Prerequisites

All examples require a video file. Download a sample:

```bash
mkdir -p assets
wget https://archive.org/download/BigBuckBunny/big_buck_bunny_720p_h264.mov \
     -O assets/big_buck_bunny_720p_h264.mov
```

## Manim Scene (`basic_scene.py`)

```bash
manim -pql examples/basic_scene.py VideoExample
```

## Manim Slides (`slide_deck.py`)

> **Note:** This example requires `manim-slides`, which is **not** installed automatically by `manim-videos`.
> Install it first:
>
> ```bash
> pip install "manim-slides[pyside6-full]"
> ```

```bash
manim-slides render -ql examples/slide_deck.py VideoSlide
manim-slides present VideoSlide
```
