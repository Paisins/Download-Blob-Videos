import aiohttp
import asyncio
import traceback
from lib import logger
from typing import List
from config import Headers, RequestConfig, ConnectorConfig, DownloaderConfig
from progress import files_progress


class Downloader:
    def __init__(self, response_handler=None):
        self.progress = files_progress
        self.task_id = None
        self.lock = asyncio.Lock()
        self.response_handler = response_handler
        self.sem = asyncio.Semaphore(DownloaderConfig["max_number"])

    def run(self, info: str, url_list: List[str], save_path_list: List[str]):
        if not url_list:
            return list()
        loop = asyncio.get_event_loop()
        self.task_id = self.progress.add_task(
            description=f"download {info}", total=len(url_list)
        )
        result = loop.run_until_complete(self.async_run(url_list, save_path_list))
        return result

    async def async_run(self, url_list: List[str], save_path_list: List[str]):
        assert len(url_list) == len(
            save_path_list
        ), "length of url_list should equals to length of save_path_list"
        with self.progress:
            # make sure session close after all request
            async with self.init_session() as session:
                tasks = list()
                for url, save_path in zip(url_list, save_path_list):
                    task = asyncio.Task(
                        self.fetch_url(
                            session=session,
                            url=url,
                            save_path=save_path,
                        )
                    )
                    tasks.append(task)
                result = await asyncio.gather(*tasks)
        return result

    async def fetch_url(
        self,
        session,
        url: str,
        retry: int = 0,
        response_handler=None,
        save_path: str = None,
    ):
        if response_handler is None:
            response_handler = self.save_as_file
        try:
            async with self.sem:
                async with session.get(url, **RequestConfig) as response:
                    if response.status != 200:
                        logger.error(f"status_code: {response.status}")
                        await asyncio.sleep(0.5)
                        return False, None
                    # not perfect yet
                    res = await response_handler(response, save_path=save_path)
                    self.progress.advance(self.task_id, advance=1)
                    # logger.info(f'SUCCESS: [{url}][save_path: {save_path}]')
                    return True, res
        except (
            asyncio.TimeoutError,
            aiohttp.client_exceptions.ServerDisconnectedError,
        ):
            if retry < DownloaderConfig["max_retry"]:
                logger.error(
                    f"FAILED: [{url}][retry: {retry+1}][error: {traceback.format_exc()}]"
                )
                return await self.fetch_url(
                    session, url, save_path=save_path, retry=retry + 1
                )
            else:
                logger.error(
                    f"FAILED: [{url}][retry_done: {retry}][error: {traceback.format_exc()}]"
                )
                return False, None
        except Exception:
            logger.error(f"FAILED: [{url}][error: {traceback.format_exc()}]")
            return False, None

    @staticmethod
    async def save_as_file(response, save_path: str = None):
        if save_path is None:
            return
        with open(save_path, "wb") as fp:
            while True:
                chunk = await response.content.read(1024)
                if not chunk:
                    break
                fp.write(chunk)

    def init_session(self):
        connector = aiohttp.TCPConnector(**ConnectorConfig)
        _session = aiohttp.ClientSession(headers=Headers, connector=connector)
        return _session
