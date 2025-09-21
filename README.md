# Download-Blob-Videos

A Python tool for downloading M3U8 blob videos with support for batch downloads and concurrent processing.

- [What is a M3U8 file?](https://docs.fileformat.com/audio/m3u8/)

## 1. Environment

- **ffmpeg** (required for merging video segments)

```shell
uv sync
```

Actually, this project only needs one package: `aiohttp`. Make sure `ffmpeg` is installed and available in your PATH.

## 2. Configuration

Edit `config.py` to configure your downloads:

```python
# Add your M3U8 URLs and desired filenames
BlobUrls = [
    (
        "https://example.com/video1.m3u8",  # M3U8 URL
        "video1.mp4",                       # Output filename
    ),
    (
        "https://example.com/video2.m3u8",
        "video2.mp4",
    ),
]

# Optional: Configure downloader settings
BlobDownloaderConfig = {
    "clean_tmp": True,  # Delete temporary files after download
}

DownloaderConfig = {
    "max_retry": 3,        # Retry attempts for failed downloads
    "max_concurrent": 20,  # Number of concurrent downloads
}
```

## 3. Usage

```shell
python3 main.py
```

This will download all videos configured in `BlobUrls` using the efficient batch processing method.

## 4. Features

- ✅ **Batch Downloads**: Download multiple videos efficiently
- ✅ **Concurrent Processing**: Parallel segment downloads
- ✅ **Retry Mechanism**: Automatic retry on failures
- ✅ **Progress Logging**: Detailed logging with code location info
- ✅ **Temporary File Management**: Optional cleanup after completion
- ✅ **Flexible Configuration**: Customizable paths and settings

## 5. Output Structure

```text
project/
├── videos/          # Final merged video files
├── tmp_files/       # Temporary files (auto-cleaned if enabled)
│   └── video_name/  # Individual video segments
```
