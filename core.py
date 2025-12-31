import os
import re
import shutil
from log import logger
from typing import Tuple
from utils import get_url_basename, get_url_prefix
from downloader import Downloader, Task
from config import DownloaderConfig


class BlobDownloader:
    """Blob video downloader that supports both single and batch downloads"""

    def __init__(self, save_path: str = "", tmp_path: str = "", clean_tmp: bool = False):
        """Initialize blob downloader

        Args:
            save_path (str): Directory to save final videos (default: ./videos)
            tmp_path (str): Directory to save temporary files (default: ./tmp_files)
            clean_tmp (bool): Whether to clean up temporary files after download (default: False)
        """
        self.base_save_path = self.gen_video_path() if not save_path else save_path
        self.base_tmp_path = self.gen_tmp_path() if not tmp_path else tmp_path
        os.makedirs(self.base_save_path, exist_ok=True)

        self.clean_tmp = clean_tmp
        # Reuse the same downloader instance for efficiency
        self.downloader = Downloader(**DownloaderConfig)

    def gen_video_path(self) -> str:
        """Generate path to save final videos

        Returns:
            str: Path to videos directory
        """
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), "videos")

    def gen_tmp_path(self) -> str:
        """Generate base path to save temporary files

        Returns:
            str: Path to temporary files directory
        """
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), "tmp_files")

    def run(self, blob_url: str, save_name: str = "") -> str:
        """Download a single blob video

        Args:
            blob_url (str): M3U8 URL to download
            save_name (str): Output filename (default: extracted from URL)

        Returns:
            str: Path to the downloaded video file
        """
        return self._download_single(blob_url, save_name)

    def run_batch(self, url_list: list) -> list[str]:
        """Download multiple blob videos

        Args:
            url_list (list): List of (url, save_name) tuples or just URLs

        Returns:
            list[str]: List of paths to downloaded video files
        """
        results = []
        for item in url_list:
            if isinstance(item, (list, tuple)) and len(item) >= 2:
                url, save_name = item[0], item[1]
            elif isinstance(item, str):
                url, save_name = item, ""
            else:
                logger.error(f"Invalid item format: {item}")
                continue

            if not save_name.endswith(".mp4"):
                save_name = f"{save_name}.mp4"

            try:
                result = self._download_single(url, save_name)
                results.append(result)
                logger.info(f"✅ Successfully downloaded: {save_name or get_url_basename(url)}")
            except Exception as e:
                logger.error(f"❌ Failed to download {url}: {e}")
                results.append(None)

        return results

    def _download_single(self, blob_url: str, save_name: str = "") -> str:
        """Internal method to download a single video

        Args:
            blob_url (str): M3U8 URL to download
            save_name (str): Output filename

        Returns:
            str: Path to the downloaded video file
        """
        # Set up instance variables for this download
        self.blob_url = blob_url.strip()
        self.save_name = get_url_basename(self.blob_url) if not save_name else save_name
        self.save_path = os.path.join(self.base_save_path, self.save_name)
        self.tmp_path = os.path.join(self.base_tmp_path, self.save_name)
        self.url_prefix = get_url_prefix(self.blob_url)

        if os.path.exists(self.save_path):
            return self.save_path

        # Create tmp directory for this specific download
        os.makedirs(self.tmp_path, exist_ok=True)

        m3u8_file = self.load_m3u8_file()
        local_m3u8_file, tasks = self.parse_m3u8_file(m3u8_file)
        self.async_load_media(tasks)
        video_path = self.merge_media(local_m3u8_file)
        if self.clean_tmp and os.path.exists(video_path):
            logger.info(f"clean up tmp_path: {self.tmp_path}")
            shutil.rmtree(self.tmp_path)
        elif not os.path.exists(video_path):
            raise Exception("merge media failed")
        return video_path

    def load_m3u8_file(self) -> str:
        """Download m3u8 file to temporary directory

        Returns:
            str: Path to downloaded m3u8 file
        """
        m3u8_file = os.path.join(self.tmp_path, get_url_basename(self.blob_url))
        if os.path.exists(m3u8_file):
            return m3u8_file
        task = Task(self.blob_url, m3u8_file)
        result = self.downloader.run(tasks=[task], desc="downloading m3u8 file")

        if len(result) == 0 or result[0] is False:
            raise Exception("failed to download m3u8 file")
        return m3u8_file

    def parse_m3u8_file(self, m3u8_file: str) -> Tuple[str, list[Task]]:
        """Parse m3u8 file and generate local m3u8 file with local paths

        Args:
            m3u8_file (str): Path to downloaded m3u8 file

        Returns:
            str: Path to local m3u8 file
            list[Task]: List of tasks to download media files
        """
        local_m3u8_file = os.path.join(self.tmp_path, "local.m3u8")
        local_m3u8 = open(local_m3u8_file, "w")

        tasks = []
        total_count = 0
        raw_m3u8 = open(m3u8_file, "r")
        for line in raw_m3u8.readlines():
            if line.startswith("#"):
                ts_url, line = self.parse_meta_data(line)
            else:
                ts_url, line = self.parse_media_segment(line)
            local_m3u8.write(line)
            if not ts_url:
                continue
            total_count += 1
            save_path = self.get_media_save_path(ts_url)
            if os.path.exists(save_path):
                continue
            tasks.append(Task(ts_url, save_path))
        logger.info(f"total: {total_count}, need to download: {len(tasks)}")
        return local_m3u8_file, tasks

    def async_load_media(self, tasks: list[Task]):
        """Download media files asynchronously

        Args:
            tasks (list[Task]): List of tasks to download media files
        """
        results = self.downloader.run(tasks=tasks, desc="downloading media files")
        failed_count = len([r for r in results if not r])
        assert (
            failed_count == 0
        ), f"""
        total task: {len(tasks)}, failed task: {failed_count}
        Please check error and retry again, some media are still not downloaded yet.
        """
        logger.info("download media success!")

    def merge_media(self, local_m3u8_file: str) -> str:
        """Merge media files into a single video file using ffmpeg

        Args:
            local_m3u8_file (str): Path to local m3u8 file with local media paths
        """
        logger.info("ffmpeg is merging...")
        cmd = """
        ffmpeg \
        -extension_picky false \
        -allowed_segment_extensions ALL \
        -protocol_whitelist "file,http,https,tcp,tls,crypto" \
        -allowed_extensions ALL \
        -i "{}" \
        -c copy "{}" \
        -loglevel quiet \
        -y
        """.format(
            local_m3u8_file, self.save_path
        )
        os.system(cmd)
        logger.info(f"finished download blob video! {self.save_path}")
        return self.save_path

    def parse_meta_data(self, line: str) -> Tuple[str, str]:
        """Parse metadata line to extract key URL and modified line

        Args:
            line (str): Metadata line from m3u8 file

        Returns:
            Tuple[str, str]: Key URL and modified line
        """
        search_res = re.search(r'URI="(.+?)"', line)
        if not search_res:
            return "", line
        key_ts = search_res.group(1)
        if "/" not in key_ts:
            key_ts_path, key_ts_name = None, key_ts
            key_url = f"{self.url_prefix}/{key_ts_name}"
        else:
            # todo can't cover all cases
            key_ts_path, key_ts_name = key_ts.rsplit("/", 1)
            if key_ts_path not in self.url_prefix:
                key_url = f"{self.url_prefix}/{key_ts}"
            else:
                part_prefix = self.url_prefix.split(key_ts_path)[0]
                key_url = f"{part_prefix}/{key_ts}"
        clean_key_ts_name = key_ts_name.split("?")[0]
        key_line = line.replace(key_ts, f"{self.tmp_path}/{clean_key_ts_name}")
        return key_url, key_line

    def parse_media_segment(self, line: str) -> Tuple[str, str]:
        """Parse media segment line to extract media URL and modified line

        Args:
            line (str): Media segment line from m3u8 file

        Returns:
            Tuple[str, str]: URL and local path
        """
        if line.startswith("http"):
            ts_url = line.rstrip()
        else:
            ts_line = line.rstrip()
            if "/" in ts_line:
                path, name = ts_line.rsplit("/", 1)
            else:
                path, name = "", ts_line
            if path not in self.url_prefix:
                ts_url = f"{self.url_prefix}/{ts_line}"
            else:
                ts_url = f"{self.url_prefix}/{name}"
        file_name = get_url_basename(ts_url)
        local_line = os.path.join(self.tmp_path, file_name) + "\n"
        return ts_url, local_line

    def get_media_save_path(self, url: str) -> str:
        """Get media save path

        Args:
            url (str): Media URL

        Returns:
            str: Media save path
        """
        save_name = get_url_basename(url)
        return os.path.join(self.tmp_path, save_name)
