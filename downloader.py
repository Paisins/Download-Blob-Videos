import aiohttp
import asyncio
import traceback
from log import logger
from typing import List
from rich.progress import TaskID
from progress import files_progress
from config import GetConfig, ConnectorConfig, HeaderConfig


class Task:
    """Task represents a download task with URL and save path"""

    url: str
    save_path: str

    def __init__(self, url: str, save_path: str) -> None:
        self.url = url
        self.save_path = save_path


class DownloadError(Exception):
    """Custom exception for download failures"""

    def __init__(self, url: str, message: str, retry_count: int = 0):
        self.url = url
        self.message = message
        self.retry_count = retry_count
        super().__init__(f"Download failed for {url}: {message} (retries: {retry_count})")


class Downloader:
    def __init__(self, max_concurrent: int = 20, max_retry: int = 3):
        """Initialize downloader with configuration parameters

        Args:
            max_concurrent (int, optional): Maximum concurrent downloads. Defaults to 20.
            max_retry (int, optional): Maximum retry attempts for failed downloads. Defaults to 3.
        """
        self.sem = asyncio.Semaphore(max_concurrent)
        self.max_retry = max_retry
        self.progress = files_progress
        self.lock = asyncio.Lock()

    def run(
        self,
        tasks: List[Task],
        desc: str = "downloading",
    ) -> List[bool]:
        """
        Run download tasks synchronously.

        Args:
            tasks: List of download tasks
            desc: Description for progress bar

        Returns:
            List[bool]: List of results, True for successful downloads, False for failed downloads
        """
        if not tasks:
            return list()
        loop = asyncio.get_event_loop()
        task_id = self.progress.add_task(description=desc, total=len(tasks))
        result = loop.run_until_complete(self.async_run(task_id, tasks))
        return result

    async def async_run(
        self,
        task_id: TaskID,
        Tasks: List[Task],
    ) -> List[bool]:
        """
        Run download tasks asynchronously.

        Args:
            Tasks: List of download tasks

        Returns:
            List[bool]: List of results, True for successful downloads, False for failed downloads
        """
        assert len(Tasks) > 0, "Tasks should not be empty"
        with self.progress:
            # make sure session close after all request
            async with self.init_session() as session:
                tasks = []
                for task_item in Tasks:
                    task = asyncio.create_task(
                        self._safe_fetch_url(
                            session=session,
                            task_id=task_id,
                            url=task_item.url,
                            save_path=task_item.save_path,
                        )
                    )
                    tasks.append(task)
                result = await asyncio.gather(*tasks)
        return result

    async def _safe_fetch_url(
        self,
        session: aiohttp.ClientSession,
        task_id: TaskID,
        url: str,
        save_path: str,
    ) -> bool:
        """
        Safe wrapper for fetch_url that handles exceptions.

        Args:
            session: aiohttp session
            url: URL to download
            save_path: path to save the file
            task_id: progress task ID

        Returns:
            Optional[bool]: True if successful, None if failed
        """
        try:
            return await self.fetch_url(session, task_id, url, save_path)
        except DownloadError as e:
            logger.error(f"Download failed: {e}")
            return False

    async def fetch_url(
        self,
        session: aiohttp.ClientSession,
        task_id: TaskID,
        url: str,
        save_path: str,
        retry: int = 0,
    ) -> bool:
        """
        Fetch URL and save to file.

        Args:
            session: aiohttp session
            url: URL to download
            task_id: progress task ID
            retry: current retry count
            save_path: path to save the file

        Returns:
            Optional[str]: save_path if successful, None if save_path is None

        Raises:
            DownloadError: if download fails after all retries
        """
        try:
            async with self.sem:
                async with session.get(url, **GetConfig) as response:
                    if response.status != 200:
                        error_msg = f"HTTP {response.status}"
                        await asyncio.sleep(0.5)
                        raise DownloadError(url, error_msg, retry)
                    await self.save_as_file(response, save_path=save_path)
                    self.progress.advance(task_id, advance=1)
                    return True
        except (
            asyncio.TimeoutError,
            aiohttp.ServerDisconnectedError,
        ) as e:
            if retry < self.max_retry:
                logger.error(f"FAILED: [{url}][retry: {retry+1}][error: {type(e).__name__}]")
                return await self.fetch_url(session, task_id, url, save_path=save_path, retry=retry + 1)
            else:
                error_msg = f"Connection error after {retry} retries: {type(e).__name__}"
                logger.error(f"FAILED: [{url}][retry_done: {retry}][error: {error_msg}]")
                raise DownloadError(url, error_msg, retry)
        except Exception as e:
            error_msg = f"Unexpected error: {type(e).__name__}"
            logger.error(f"FAILED: [{url}][error: {traceback.format_exc()}]")
            raise DownloadError(url, error_msg, retry)

    async def save_as_file(self, response: aiohttp.ClientResponse, save_path: str):
        """
        Save response content to file.

        Args:
            response: aiohttp response object
            save_path: path to save the file

        Returns:
            Optional[str]: save_path if file was saved, None if save_path is None
        """
        with open(save_path, "wb") as fp:
            while True:
                chunk = await response.content.read(1024)
                if not chunk:
                    break
                fp.write(chunk)

    def init_session(self) -> aiohttp.ClientSession:
        """Initialize aiohttp session with configured headers and connector.

        Returns:
            aiohttp.ClientSession: Configured aiohttp session
        """
        connector = aiohttp.TCPConnector(**ConnectorConfig)
        _session = aiohttp.ClientSession(headers=HeaderConfig, connector=connector)
        return _session
