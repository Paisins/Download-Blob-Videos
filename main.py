from config import BlobUrls
from core import BlobDownloader


def main():
    # 方式1: 批量下载（推荐）
    downloader = BlobDownloader(clean_tmp=True)
    results = downloader.run_batch(BlobUrls)

    # 方式2: 单个下载
    # downloader = BlobDownloader()
    # for url, save_name in BlobUrls:
    #     downloader.run(url, save_name)

    successful_downloads = [r for r in results if r is not None]
    print(f"✅ Successfully downloaded {len(successful_downloads)}/{len(BlobUrls)} videos!")
    print("🎉 Download completed!")


if __name__ == "__main__":
    main()
