import os
import argparse
import requests
from coroutine_download import coroutine_download


def download_file(url, save_name):
    response = requests.get(url)
    with open(save_name, 'w') as f:
        f.write(response.text)

def gen_download_list(ts_list_path, save_name, m3u8_url):
    download_file(m3u8_url, os.path.join(ts_list_path, f'{save_name}.m3u8'))
    ts_url_pre = '/'.join(m3u8_url.split('?')[0].split('/')[:-1])

    ts_list = list()
    save_file = open(os.path.join(ts_list_path, f'{save_name}_download.txt'), 'w')
    for line in open(os.path.join(ts_list_path, f'{save_name}.m3u8'), 'r'):
        if line.startswith('#'):
            continue
        # save_file.write(f'{ts_url_pre}/{os.path.basename(line)}')
        save_file.write(f'{ts_url_pre}/{line}')
        # ts_list.append(f'{ts_url_pre}/{os.path.basename(line)}'.rstrip())
        ts_list.append(f'{ts_url_pre}/{line.rstrip()}')
    save_file.close()
    return ts_list


def get_video(project_path, save_name, ts_url_pre):
    ts_local_name = os.path.join(project_path, 'ts_list_files', f'{save_name}_local.txt')
    ts_local_file = open(ts_local_name, 'w')
    ts_file = open(os.path.join(project_path, 'ts_list_files', f'{save_name}.m3u8'), 'r')

    save_path = os.path.join(project_path, 'ts_video_tmp')

    for i in range(4):
        ts_local_file.write(ts_file.readline())
    
    # 解密文件
    line = ts_file.readline()
    if 'URI="' in line:
        key_ts_name = line.split('"')[1]
        
        download_file(os.path.join(ts_url_pre, key_ts_name), os.path.join(project_path, 'ts_list_files', key_ts_name))
        ts_local_file.write(line.replace('URI="', f'URI={project_path}/ts_key_files/'))
    else:
        ts_local_file.write(line)

    for line in ts_file:
        if '?' in line:
            line = line.split('?')[0] + '\n'
        if not line.rstrip().endswith('ts'):
            ts_local_file.write(line)
        else:
            ts_local_file.write(os.path.join(save_path, save_name, os.path.basename(line.rstrip())) + '\n')
            # break
    ts_local_file.close()

    save_path = os.path.join(project_path, 'videos', f'{save_name}.mp4')
    cmd = 'ffmpeg -i {} -c copy {} -loglevel quiet'.format(ts_local_name, save_path)

    print(cmd)
    os.system(cmd)
    return save_path


def main(args):
    save_name = args.save_name
    m3u8_url = args.url
    project_path = args.project_path
    max_workers = args.max_workers

    ts_video_path = os.path.join(project_path, 'ts_video_tmp', save_name)
    ts_list_path = os.path.join(project_path, 'ts_list_files')
    ts_key_path = os.path.join(project_path, 'ts_key_files')
    videos_path = os.path.join(project_path, 'videos')

    os.makedirs(ts_video_path, exist_ok=True)
    os.makedirs(ts_list_path, exist_ok=True)
    os.makedirs(ts_key_path, exist_ok=True)
    os.makedirs(videos_path, exist_ok=True)

    ts_list_path = os.path.join(project_path, 'ts_list_files')
    ts_list = gen_download_list(ts_list_path, save_name, m3u8_url)
    total_download_count = len(ts_list)
    already_download_count = len(os.listdir(ts_video_path))
    need_download_count = total_download_count - already_download_count
    print('共{}个ts需要下载, 已下载{}个，还需要下载{}个'.format(total_download_count, already_download_count, need_download_count))


    coroutine_download(ts_list, ts_video_path, max_workers)

    download_count = len(os.listdir(ts_video_path))
    fail_count = total_download_count-download_count
    print('下载完成{}个， 缺失{}个'.format(download_count, fail_count))

    if fail_count > 0:
        print('请重新下载，待ts全部下载完成后再合并')
        return

    print('开始合并...')
    ts_url_pre = '/'.join(m3u8_url.split('/')[:-1])
    save_path = get_video(project_path, save_name, ts_url_pre)
    print(f'合并成功! 保存为{save_path}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-save_name', help='保存视频名称', type=str, required=True)
    parser.add_argument('-url', help='m3u8文件的url', type=str, required=True)
    parser.add_argument('-project_path', help='下载目录，存放一些中间文件', type=str, default='./')
    parser.add_argument('-max_workers', help='下载线程数', type=int, default=3)
    args = parser.parse_args()
    main(args)



