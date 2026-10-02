# Random Image Auto Downloader

A small desktop app that automatically downloads random images from
[picsum.photos](https://picsum.photos) on a timer. Pure Python, no API keys.

## Features

- Random photos on a fixed interval, in the size you choose
- Run a fixed count or loop forever (`0`)
- Blur (0-10) and grayscale options
- Live preview of each downloaded image
- Threaded downloads with interruptible stop and automatic retries
- Shows the resolved save path in the status bar, so you always know where
  images are being written
- Refuses to start if the chosen folder is missing or not writable
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
pick another folder, or type a path straight into the **Save to** box.

### Controls

| Control | Meaning |
| --- | --- |
| Size | Output resolution, from `640x480` to `1920x1080` |
| Count | How many images to fetch. `0` runs until you press **Stop** |
| Interval | Seconds between downloads (minimum `0.2`) |
| Blur | `0-10`, passed to Picsum's blur filter |
| Grayscale | Downloads in black and white |

**One image** grabs a single photo without starting the loop. **Open folder**
reveals the save location in Explorer.

### Where files went

The status bar always ends with the folder that was written to, for example:

```
Finished (20 saved) -> C:\Users\you\Pictures\random
```

The log repeats it on the first download of each run. If you picked a folder
and the images aren't there, this line tells you immediately whether the app
ignored your choice or wrote somewhere else.

## Notes

Images come from Lorem Picsum, which serves photos from Unsplash. Check
[Lorem Picsum's license](https://picsum.photos/#license) before commercial use.
