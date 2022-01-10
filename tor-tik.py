#!/usr/bin/env python3
import argparse
import os
import shutil
import sys
import subprocess

from TikTokApi import TikTokApi
api = TikTokApi.get_instance()

FFMEG_CONFIG = "ffmeg_input.txt"
OUT_BASE_NAME = "out"

logo = """
 ______   ___   ____                  ______  ____  __  _ 
|      T /   \ |    \                |      Tl    j|  l/ ]
|      |Y     Y|  D  )     _____     |      | |  T |  ' / 
l_j  l_j|  O  ||    /     |     |    l_j  l_j |  | |    \ 
  |  |  |     ||    \     l_____j      |  |   |  | |     Y
  |  |  l     !|  .  Y                 |  |   j  l |  .  |
  l__j   \___/ l__j\_j                 l__j  |____jl__j\_j
"""

# def init_global_api()

class TikTok():
    def __init__(self, url, tid, description):
        self.url = url
        self.tid = tid
        self.description = description
        self.api_info = api.get_tiktok_by_id(self.tid) # construct tic-tok dict
        # XXX: extract it from file itself to remove api dependency?
        self.duration = self.api_info['itemInfo']['itemStruct']['video']['duration']

    @classmethod
    def from_url(cls, url):
        return cls(url, TikTok.url2id(url), "")

    @staticmethod
    def url2id(url):
        return int(url.split("/video/")[1].split("?")[0])

    @staticmethod
    def fname_from_tid(download_dir, tid):
        return os.path.join(download_dir, f"{tid}.mp4")

    def download(self, download_dir):
        out_file = TikTok.fname_from_tid(download_dir, self.tid)
        # caching(sort of)
        if os.path.exists(out_file):
            return out_file
        data = api.get_video_by_tiktok(self.api_info)
        with open(out_file, 'wb') as output:
            output.write(data) # saves data to the mp4 file
        return out_file

def parse_file(filename):
    """
    parse text file to inner structure in following way:
    - any line that starts with `TIK_TOK_LINK_LINE` will be interpreted as link
      to tiktok video
    - all following non-empty lines will be interpreted as description and will
      be put to subtitles file
    """
    TIK_TOK_LINK_LINE = "https://www.tiktok.com"
    tt = None
    with open(filename) as f:
        for line in f.readlines():
            if line.startswith(TIK_TOK_LINK_LINE):
                # new tiktok found, yield exisiting
                if tt is not None:
                    yield tt
                tt = TikTok.from_url(line)
            elif line.strip():
                if tt is None:
                    continue
                tt.description += line
    if tt is not None:
        yield tt


def intersperse(lst, item):
    """
    Insert item between each element it lst
    """
    result = [item] * (len(lst) * 2 - 1)
    result[0::2] = lst
    return result

def gen_ffmpeg_config_file(out_files, out_dir):
    ff_lines = []
    for of in out_files:
        ff_lines.append(f"file '{os.path.basename(of)}'\n")

    ff_config_full_path = os.path.join(out_dir, FFMEG_CONFIG)
    with open(ff_config_full_path, 'w') as f:
            f.writelines(ff_lines)
    return ff_config_full_path

def ffmpeg_convert_to_mts(inputfile):
    outfile = inputfile.replace(".mp4", ".mts")
    # XXX: think more about this scale, for now it will set the width of 720px
    # and the height will be set based on the ratio of the original video
    # subprocess.check_output(["ffmpeg", "-i", inputfile, "-vf", "scale=-1:720", "-y", "-q", "0",
    subprocess.check_output(["ffmpeg", "-i", inputfile, "-y", "-q", "0",
        outfile])
    return outfile

def ffmpeg_concat(ffmpeg_config, out_dir):
    subprocess.check_output(["ffmpeg", "-f", "concat", "-i", ffmpeg_config,
        "-y", "-c", "copy", f"{out_dir}/{OUT_BASE_NAME}.mp4"])

def concat_all(files, out_dir, transition):
    # convert all to mts format to concatenate it later without any problems,
    # XXX: not sure this is the best way to do this:
    # https://video.stackexchange.com/questions/15468/non-monotonous-dts-on-concat-ffmpeg
    out_files = [ffmpeg_convert_to_mts(f) for f in files]
    if transition is not None:
        transition = ffmpeg_convert_to_mts(transition)
        out_files = intersperse(out_files, transition)
    ffmpeg_config = gen_ffmpeg_config_file(out_files, out_dir)
    ffmpeg_concat(ffmpeg_config, out_dir)

def generating_subs(files, out_dir, transition_duration):
    file_name = "{out_dir}/{OUT_BASE_NAME}.srt"

def main(config):
    # tiktoks = [TikTok.from_url(url) for url in get_urls_from_list(config.input)]
    tiktoks = list(parse_file(config.input))
    download_dir = config.output
    transition = None

    if config.transition is not None:
        transition = os.path.join(download_dir,
                os.path.basename(config.transition))
        shutil.copyfile(config.transition, transition)
        # subprocess.check_output(["cp", config.transition, download_dir])

    print(f"Number of tik-toks: {len(tiktoks)}")
    print("Downloading...")
    out_files = []
    for tt in tiktoks:
        print(f"url: '{tt.url}', desc: '{tt.description}'")
        continue
        try:
            out_files.append(tt.download(download_dir))
            print(f"{tt.tid} done")
        except:
            out_files.pop()
            print(f"{tt.tid} fail")

    print("generating full video...")
    # concat_all(out_files, download_dir, transition)
    print("generating subs...")
    generate_subs(out_files, download_dir)
    print("DONE!")

def parse_args(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", required=True, dest="input",
        help="Input list file of tic-toks", type=str)
    parser.add_argument("-o", "--output", required=True, dest="output",
        help="Output directory, where will stored all the results", type=str)
    parser.add_argument("-t", "--transition", required=False,
            dest="transition", type=str, default=None,
            help="Transition video(will be inserted after each tic-tok)")
    args = parser.parse_args()
    if not os.path.exists(args.output):
        os.mkdir(args.output)
        print(f"Directory: {args.output} do not exist")
    return args

if __name__ == "__main__":
    print(logo)
    config = parse_args(sys.argv)
    main(config)
