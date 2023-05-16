import os
import re
import shutil
from lib import logger
from utils import get_url_prefix, get_url_basename, generate_save_path
from downloader import Downloader
from config import BlobUrl, SaveVideoName, DownloaderConfig


class BlobDownloader:
    """
    get all urls of ts files from m3u8 file, and use ffmpeg to merge them to one video
    """

    def __init__(self, blob_url: str = None, save_name: str = None):
        self.blob_url = blob_url.strip() if blob_url else BlobUrl.strip()

        if save_name:
            self.save_name = save_name
        elif SaveVideoName:
            self.save_name = SaveVideoName
        else:
            self.save_name = get_url_basename(self.blob_url)

        # path to save final videos
        self.video_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "videos"
        )
        # path to save temporary files, like *.ts file
        self.tmp_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "tmp_files", self.save_name
        )
        os.makedirs(self.video_path, exist_ok=True)
        os.makedirs(self.tmp_path, exist_ok=True)

        self.downloader = Downloader()
        self.url_prefix = get_url_prefix(self.blob_url)

    def run(self):
        m3u8_file = self.fetch_m3u8_file()
        local_m3u8_file = self.parse_m3u8_file(m3u8_file)
        self.decode_to_video(local_m3u8_file)
        if DownloaderConfig.get("clean"):
            logger.info(f"clean up tmp_path: {self.tmp_path}")
            shutil.rmtree(self.tmp_path)

    def fetch_m3u8_file(self):
        save_name = get_url_basename(self.blob_url)
        save_path = os.path.join(self.tmp_path, save_name)
        if os.path.exists(save_path):
            return save_path

        url_list, save_path_list = [self.blob_url], [save_path]
        result = self.downloader.run(
            "m3u8 file", url_list=url_list, save_path_list=save_path_list
        )

        if result[0][0] is False:
            raise Exception("failed to download m3u8 file")
        return save_path

    def parse_m3u8_file(self, m3u8_file: str):
        """
        parse m3u8 file to get all ts url and transfer it to a local path
        """
        ts_urls = list()
        save_path_list = list()
        local_m3u8_lines = list()
        total_count, success_count = 0, 0
        with open(m3u8_file, "r") as f:
            for line in f:
                if line.startswith("#"):
                    search_res = re.search(r'URI="(.+?)"', line)
                    if search_res:
                        key_ts = search_res.group(1)
                        if "/" not in key_ts:
                            key_ts_path, key_ts_name = None, key_ts
                        else:
                            key_ts_path, key_ts_name = key_ts.rsplit("/", 1)
                        if key_ts_path and key_ts_path not in self.url_prefix:
                            ts_url = f"{self.url_prefix}/{key_ts}"
                        else:
                            ts_url = f"{self.url_prefix}/{key_ts_name}"
                        key_line = line.replace(
                            key_ts, f"{self.tmp_path}/{key_ts_name}"
                        )
                        local_m3u8_lines.append(key_line)
                    else:
                        ts_url = None
                        local_m3u8_lines.append(line)
                else:
                    if line.startswith("http"):
                        ts_url = line.rstrip()
                    else:
                        ts_line = line.rstrip()
                        if "/" in ts_line:
                            path, name = ts_line.rsplit("/", 1)
                        else:
                            path = ""
                            name = ts_line
                        if path not in self.url_prefix:
                            ts_url = f"{self.url_prefix}/{ts_line}"
                        else:
                            ts_url = f"{self.url_prefix}/{name}"
                    local_m3u8_lines.append(
                        os.path.join(self.tmp_path, get_url_basename(ts_url)) + "\n"
                    )

                if not ts_url:
                    continue
                total_count += 1
                save_path = generate_save_path(ts_url, self.tmp_path)

                if os.path.exists(save_path):
                    success_count += 1
                    continue
                ts_urls.append(ts_url)
                save_path_list.append(save_path)

        local_m3u8_file = os.path.join(self.tmp_path, "local_m3u8.txt")
        with open(local_m3u8_file, "w") as f:
            for line in local_m3u8_lines:
                f.write(line)

        # logger.info(f'total: {total_count}, need to download: {len(ts_urls)}')
        results = self.downloader.run(
            "ts files", url_list=ts_urls, save_path_list=save_path_list
        )

        success_count += len([r[0] for r in results if r[0]])
        assert (
            success_count == total_count
        ), f"""
        total ts files: {total_count}, success ts files: {success_count}
        Please check error and retry again, some ts files are still not downloaded yet.
        """
        logger.info("Download finished!")
        return local_m3u8_file

    def decode_to_video(self, local_m3u8_file: str):
        save_path = os.path.join(self.video_path, self.save_name)
        logger.info("ffmpeg is merging...")

        cmd = 'ffmpeg -allowed_extensions ALL -i "{}" -c copy "{}" -loglevel quiet -y'.format(
            local_m3u8_file, save_path
        )
        os.system(cmd)
        # i tried ffmpeg-python, but really don't know to make it work. it's too slow
        # ffmpeg.input(local_m3u8_file).concat().output(save_path).global_args('-report').run(overwrite_output=True)  # quiet=True
        logger.info(f"finished download blob video! {save_path}")


if __name__ == "__main__":
    blob_downloader = BlobDownloader()
    blob_downloader.run()
