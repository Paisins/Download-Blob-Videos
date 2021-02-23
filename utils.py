import os
from typing import List


def get_url_prefix(url):
    # generally m3u8 file and ts files are in same directory
    return '/'.join(url.split('?')[0].split('/')[:-1])


def get_url_basename(url: str):
    """get save file name for url"""
    return os.path.basename(url.split('?')[0])


def generate_save_path_list(url_list: List[str], save_folder: str):
    """generate save file path for urls given the folder to save files"""
    save_path_list = list()
    os.makedirs(save_folder, exist_ok=True)
    for url in url_list:
        save_path = generate_save_path(url, save_folder)
        save_path_list.append(save_path)


def generate_save_path(url: str, save_folder: str):
    save_name = get_url_basename(url)
    save_path = os.path.join(save_folder, save_name)
    return save_path
