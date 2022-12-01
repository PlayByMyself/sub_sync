import argparse
import logging
import os
import subprocess
from hashlib import md5
from typing import List, Optional, Set, Tuple

from sub_sync import __version__


def extend_list_from_env(base_list: List[str], env_key: str) -> None:
    env_value = os.environ.get(env_key)
    if not env_value:
        return
    extend_list = env_value.split(" ")
    base_list.extend(extend_list)
    base_list = list(set(base_list))


SUB_EXT_LIST: List[str] = ["zh.ass", "zh.srt"]
VIDEO_EXT_LIST: List[str] = ["mkv", "mp4"]
BACKUP_SUB_EXT = "sub_sync_back"

extend_list_from_env(SUB_EXT_LIST, "SUB_EXT_LIST")
extend_list_from_env(VIDEO_EXT_LIST, "SUB_EXT_LIST")

LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"

logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)


def sub_sync(dir: str) -> None:
    logging.info("start process " + dir)
    for root, _, files in os.walk(
        dir, followlinks=True, onerror=walk_error_handler
    ):
        if len(files) == 0:
            continue
        all_files = [os.path.join(root, file) for file in files]
        sub_files = filter(end_with_sub_ext, all_files)
        video_files = set(filter(end_with_video_ext, all_files))
        backup_sub_files = set(filter(end_with_backup_sub_ext, all_files))
        for sub_file in sub_files:
            process_sub_file(sub_file, video_files, backup_sub_files)


def walk_error_handler(exception_instance) -> None:
    logging.error(exception_instance)


def process_sub_file(
    sub_file: str, video_files: Set[str], backup_sub_files: Set[str]
) -> None:
    result = split_sub_file(sub_file)
    # if not match, skip
    if result is None:
        logging.info(sub_file + " not matched, skip it")
        return
    basename, _ = result
    # if processed, skip
    backup_sub_file = "{}.{}".format(sub_file, BACKUP_SUB_EXT)
    if backup_sub_file in backup_sub_files:
        logging.info(sub_file + " processed, skip it")
        return
    # if video not exist, skip
    video_file = get_video_file(basename, video_files)
    if video_file is None:
        logging.info(sub_file + " no relate video, skip it")
        return
    run_cmd(["cp", sub_file, backup_sub_file])
    try:
        run_cmd(["ffs", video_file, "-i", sub_file, "-o", sub_file])
    except Exception as e:
        logging.error(e)
        logging.info(
            "revert "
            + backup_sub_file
            + " to "
            + sub_file
            + " because sync subtitle failed"
        )
        revert_file(sub_file, backup_sub_file)
    finally:
        if file_md5(sub_file) == file_md5(backup_sub_file):
            logging.info(
                "revert "
                + backup_sub_file
                + " to "
                + sub_file
                + " because file not change"
            )
            revert_file(sub_file, backup_sub_file)


def revert_file(sub_file: str, backup_sub_file: str) -> None:
    if os.path.isfile(backup_sub_file):
        if os.path.isfile(sub_file):
            os.remove(sub_file)
        run_cmd(["mv", backup_sub_file, sub_file])


def file_md5(file_path: str) -> str:
    with open(file_path, "rb") as file:
        data = file.read()
    return md5(data).hexdigest()


def run_cmd(cmd: List[str]) -> None:
    result = subprocess.run(cmd)
    if result.returncode != 0:
        raise Exception(
            "CMD: "
            + " ".join(cmd)
            + " run failed, exit: "
            + str(result.returncode)
        )
    logging.info("CMD: " + " ".join(cmd) + " finished")


def get_video_file(basename: str, video_files: Set[str]) -> Optional[str]:
    for video_file in map(
        lambda video_ext: "{}.{}".format(basename, video_ext), VIDEO_EXT_LIST
    ):
        if video_file in video_files:
            return video_file
    return None


def split_sub_file(sub_file: str) -> Optional[Tuple[str, str]]:
    for sub_ext in SUB_EXT_LIST:
        if end_with_ext(sub_file, sub_ext):
            ext_len = len(sub_ext) + 1
            return sub_file[:-ext_len], sub_ext
    return None


def end_with_sub_ext(s: str) -> bool:
    if s is None:
        return False
    return any(map(lambda sub_ext: end_with_ext(s, sub_ext), SUB_EXT_LIST))


def end_with_video_ext(s: str) -> bool:
    if s is None:
        return False
    return any(map(lambda ext: end_with_ext(s, ext), VIDEO_EXT_LIST))


def end_with_backup_sub_ext(s: str) -> bool:
    if s is None:
        return False
    return end_with_ext(s, BACKUP_SUB_EXT)


def end_with_ext(name: str, ext: str) -> bool:
    return name.lower().endswith("." + ext)


def sync_sub_on_dirs(dirs: List[str]) -> None:
    for dir in dirs:
        sub_sync(dir)


def main() -> None:
    parser = argparse.ArgumentParser(description="sync subtitles by video")
    parser.add_argument(
        "dirs",
        type=str,
        nargs="+",
        default=os.environ.get("SYNC_DIRS"),
        help="sync subtile in dirs",
    )
    parser.add_argument("--version", action="version", version=__version__)
    args = parser.parse_args()
    sync_sub_on_dirs(args.dirs)
