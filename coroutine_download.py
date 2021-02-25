import os
import time
import math
import requests
import asyncio
from requests.adapters import HTTPAdapter
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed


def time_format(seconds):
    hour = seconds // 3600
    minute = (seconds - hour * 3600) // 60
    seconds = seconds - hour * 3600 - minute * 60
    return f'{hour:.0f}小时{minute:.0f}分钟{seconds:.1f}秒'


async def download(s, ts_url, save_ts, headers):
    # print(repr(ts_url))
    response = s.get(ts_url, timeout=3, headers=headers)
    if response.status_code != 200:
        print('status_code: ', response.status_code)
    else:
        with open(save_ts, 'wb') as f:
            f.write(response.content)
    global count, t1
    if count % 100 == 0:
        time_cost = time_format(time.time() - t1)
        print(f'已下载：{count}, 耗时{time_cost}')
    count += 1

async def download_ts(s, ts_url, headers, save_path):
    save_ts = os.path.join(save_path, os.path.basename(ts_url.split('?')[0]))
    if os.path.exists(save_ts):
        return
    await download(s, ts_url, save_ts, headers)


def muluti_threading_task(pool_executor, func, seesion, headers, ts_lists, save_path, max_workers=4):
    print(f'max_workers: {max_workers}')
    with pool_executor(max_workers=max_workers) as executor:
        tasks = [executor.submit(func, seesion, ts_list, headers, save_path) for ts_list in ts_lists]
        for task in as_completed(tasks):
            try:
                task.result()
            except Exception as exc:
                print('error: ', exc)


def coroutine_main(session, ts_list, headers, save_path):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    tasks = [download_ts(session, ts_url, headers, save_path) for ts_url in ts_list]
    loop.run_until_complete(asyncio.gather(*tasks))
    # loop.close()


def coroutine_download(total_ts, save_path, max_workers=6):
    global count, t1
    count = 0

    s = requests.Session()
    s.mount('http://', HTTPAdapter(max_retries=3))
    s.mount('https://', HTTPAdapter(max_retries=3))

    headers = {'user-agent': ''}

    split_piece = max_workers
    split_num = math.ceil(len(total_ts) / split_piece)

    ts_lists = [total_ts[i:i+split_num] for i in range(0, len(total_ts), split_num)]

    t1 = time.time()
    muluti_threading_task(ThreadPoolExecutor, coroutine_main, s, headers, ts_lists, save_path, max_workers=max_workers)


