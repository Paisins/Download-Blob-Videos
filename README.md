# Download-Blob-Videos

## 一、安装ffmpeg
网上教程很多

## 二、修改coroutine_download.py中的headers
```
headers = {'user-agent': ''}
```
## 三、执行命令
```
python3 main_download.py -project_path='save_path' -save_name='video_name' -url='m3u8_url'
```

## 注意事项
1、如果是简单的m3u8文件，可以使用
```	ffmpeg -i {m3u8_url} {video.mp4}```
这样的命令直接下载，但是如果m3u8包括的ts文件较多，网络不太稳定的时候不推荐这样下载，因为中断后需要重新下载

2、ts_key_path一般是下载的ts文件需要解密时才会用到的

3、如果在使用开发者工具时网页提示```Paused in debugger```，选中开发者工具中的```Deactivate Breakpoints```，然后刷新页面即可。
