import logging

# logger
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d:%(funcName)s] - %(message)s"
)

logger = logging.getLogger("download_blob_videos")
