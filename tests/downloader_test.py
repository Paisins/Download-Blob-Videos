from config import DownloaderConfig
from downloader import Downloader, Task


def test_downloader():
    downloader = Downloader(**DownloaderConfig)
    tasks = [Task(url="", save_path="")]
    downloader.run(tasks=tasks, desc="test")
