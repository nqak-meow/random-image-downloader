# Random Image Auto Downloader

A small desktop app that automatically downloads random images from
[picsum.photos](https://picsum.photos) on a timer. Pure Python, no API keys.

![screenshot](screenshot.png)

## Features

- Random photos on a fixed interval, in the size you choose
- Run a fixed count or loop forever (`0`)
- Blur (0-10) and grayscale options
- Live preview of each downloaded image
- Threaded downloads with interruptible stop and automatic retries
- Writes history to `~/Downloads/random_images_history.json`

## Requirements

- Python 3.9+
- [Pillow](https://pypi.org/project/Pillow/) — optional, only for the preview pane

```bash
pip install pillow
```

## Run

```bash
python image_downloader.py
```

Images are saved to `~/Downloads/random_images` by default. Use **Browse** to
pick another folder.

## Notes

Images come from Lorem Picsum, which serves photos from Unsplash. Check
[Lorem Picsum's license](https://picsum.photos/#license) before commercial use.
