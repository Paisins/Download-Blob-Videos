BlobUrls = [
    (
        # change this to your blob url
        "",
        # default format: mp4
        "",
    ),
]


# DownloaderConfig
DownloaderConfig = {
    "max_retry": 3,  # if failed as expected error, retry download
    "max_concurrent": 20,  # the number of files downloaded at same time
}

# to avoid timeout error, please always consider about the size of files
# if the size of every single file is large, you should decrease max_concurrent
# 1. limit the number of downloading file at same time
# 2. increase timeout
# 3. choose a proper connection limit
HeaderConfig = {
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 11_2_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Safari/537.36"
}
GetConfig = {
    # "proxy": "http://127.0.0.1:7897",
}

ConnectorConfig = {
    "verify_ssl": False,
    "limit": 5,  # control the connection limit
}
