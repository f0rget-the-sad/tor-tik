#!/usr/bin/env python3
import argparse
import os
import sys
import subprocess

from TikTokApi import TikTokApi
api = TikTokApi.get_instance()

FFMEG_CONFIG = "ffmeg_input.txt"

logo = """
 ______   ___   ____                  ______  ____  __  _ 
|      T /   \ |    \                |      Tl    j|  l/ ]
|      |Y     Y|  D  )     _____     |      | |  T |  ' / 
l_j  l_j|  O  ||    /     |     |    l_j  l_j |  | |    \ 
  |  |  |     ||    \     l_____j      |  |   |  | |     Y
  |  |  l     !|  .  Y                 |  |   j  l |  .  |
  l__j   \___/ l__j\_j                 l__j  |____jl__j\_j
"""

def url2id(url):
    return int(url.split("/video/")[1].split("?")[0])

def fname_from_tid(download_dir, tid):
    return f"{download_dir}/{tid}.mp4"

def download(tid, out_file):
    tt = api.get_tiktok_by_id(tid) # construct tic-tok dict
    data = api.get_video_by_tiktok(tt)
    with open(out_file, 'wb') as output:
        output.write(data) # saves data to the mp4 file

def get_urls_from_list(filename):
    with open(filename) as f:
        for line in f.readlines():
            if line.startswith("https://www.tiktok.com"):
                yield line

def gen_ffmpeg_config_file(out_files, download_dir):
    ff_lines = []
    for of in out_files:
        ff_lines.append(f"file '{os.path.basename(of)}'\n")
        # XXX: separator have some issues with merging, probably related to
        # the resolution or format
        # ff_lines.append("file 'separator.mkv'\n")

    ff_config_full_path = f"{download_dir}/{FFMEG_CONFIG}"
    with open(ff_config_full_path, 'w') as f:
            f.writelines(ff_lines)
    return ff_config_full_path


def main(config):
    tids = [url2id(url) for url in get_urls_from_list(config.input)]
    download_dir = config.output

    print(f"Number of tic-toks: {len(tids)}")
    print("Downloading...")
    out_files = []
    for tid in tids:
        # caching(sort of)
        out_file = fname_from_tid(download_dir, tid)
        out_files.append(out_file)
        if os.path.exists(out_file):
            continue
        try:
            download(tid, out_file)
            print(f"{tid} done")
        except:
            out_files.pop()
            print(f"{tid} fail")

    print("generating full video...")
    ffmpeg_file = gen_ffmpeg_config_file(out_files, download_dir)
    subprocess.check_output(["ffmpeg", "-f", "concat", "-i", ffmpeg_file,
        "-y", "-c", "copy", f"{download_dir}/out.mp4"])

def parse_args(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", required=True, dest="input",
        help="Input list file of tic-toks", type=str)
    parser.add_argument("-o", "--output", required=True, dest="output",
        help="Output directory, where will stored all the results", type=str)
    args = parser.parse_args()
    if not os.path.exists(args.output):
        os.mkdir(args.output)
        print(f"Directory: {args.output} do not exist")
    return args

if __name__ == "__main__":
    config = parse_args(sys.argv)
    print(logo)
    main(config)
