"""
Blob Downloader Config
"""

# change this to your blob url
BlobUrl = ""
# default format: mp4
SaveVideoName = "video_name.mp4"

Headers = {
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 11_2_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Safari/537.36"
}

# to avoid timeout error, please always consider about the size of files
# if the size of every single file is large, you should decrease max_number
# 1. limit the number of downloading file at same time
# 2. increase timeout
# 3. choose a proper connection limit

RequestConfig = {
    # 'proxy': 'http://127.0.0.1:7890',
    "timeout": 60 * 3
}

DownloaderConfig = {
    "max_retry": 3,  # if failed as expected error, retry download
    "max_number": 20,  # the number of files downloaded at same time
    "clean": True,
}

ConnectorConfig = {
    "verify_ssl": False,
    "limit": 5,  # control the connection limit
}
