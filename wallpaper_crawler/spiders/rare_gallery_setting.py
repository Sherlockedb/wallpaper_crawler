from pathlib import Path

REQUEST_STORE = '/Users/sherlock/Project/wallpaper_crawler/.request/iu_iph_wallpaper_request.json'  # 请求信息保存路径
IMAGES_STORE = '/Users/sherlock/Project/wallpaper_crawler/iu_iph_wallpaper'  # 图片保存的文件夹


def _check_dir(directory):
    if directory.exists():
        return
    directory.mkdir(parents=True)  # parents=True 允许创建多层目录

def check_dir(dir_path):
    directory = Path(dir_path)
    return _check_dir(directory)


def check_file_dir(file):
    file_path = Path(file)
    directory = file_path.parent  # 提取文件的父目录
    return _check_dir(directory)


check_file_dir(REQUEST_STORE)
check_dir(IMAGES_STORE)