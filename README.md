# Download-Blob-Videos

## 1. Environment

- python3
- ffmpeg

```shell
pip install -r requirement.txt
```

Actually, this project only need to install one package: aiohttp. `ffmpeg` should be installed before downloading.

## 2. Run

First of all, change `config.py` and write down the blob video url to download, and the video name to be saved as. A blob url always end with `.m3u8`.

```python
BlobUrl = ''
SaveVideoName = "video_name.mp4"
```

Secondly, run this

```shell
python3 blob_downloader.py
```

This project is far away from perfect, even a little change of website could crash all downloading tasks. For now, it is only used to help myself download some videos.

## 3. TODO

- [ ] add log color，able to skip some info
- [X] capture concurrent.futures._base.TimeoutError and retry
- [X] should i clean all tmp files? what if failed?
