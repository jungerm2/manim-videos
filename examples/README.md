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

## Comparison between Manim Videos and using ImageMobjects to play a video (`trailer.py`)

To render the big bunny trailer example from the quickstart guide:
```bash
manim -pql examples/trailer.py Trailer
```

Which takes ~47 seconds on my (very old) laptop. Meanwhile, rendering the videos out frame-by-frame using ImageMobjects takes ~3:15 minutes:

```bash
manim -pql examples/trailer_slow.py TrailerSlow
```

Not only is it much slower, but it also plays back at the wrong speed:
```
WARNING  The original duration of TrailerSlow.wait(), 0.0416667 seconds, is too    scene.py:1118
          short for the current frame rate of 15 FPS. Rendering with the shortest                
          possible duration of 0.0666667 seconds instead.  
```

...and it's much harder to play animations at the same time (here the replacement transform happens before the playback).
