#!/usr/bin/env python3
import argparse
import json
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
        self.api_info = None
        self.duration = 0
        self.local_file = None

    @classmethod
    def from_url(cls, url):
        return cls(url, None, "")

    @staticmethod
    def url2id(url):
        return int(url.split("/video/")[1].split("?")[0])

    @staticmethod
    def fname_from_tid(download_dir, tid):
        return os.path.join(download_dir, f"{tid}.mp4")

    def download(self, download_dir):
        self.tid = TikTok.url2id(self.url)
        out_file = TikTok.fname_from_tid(download_dir, self.tid)
        # caching(sort of)
        if not os.path.exists(out_file):
            self.api_info = api.get_tiktok_by_id(self.tid)
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
        for n, line in enumerate(f.readlines()):
            print(n)
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

def ffmpeg_format_info(inputfile):
    output = subprocess.check_output(["ffprobe", "-v", "quiet", "-show_format",
        "-print_format", "json", "-i", inputfile], text=True)
    return json.loads(output)

def ffmpeg_convert_to_mts(inputfile):
    outfile = inputfile.replace(".mp4", ".mts")
    if not os.path.exists(outfile):
        subprocess.check_output(["ffmpeg", "-i", inputfile, "-q", "0", outfile])
    return outfile

def ffmpeg_concat(ffmpeg_config, out_dir):
    subprocess.check_output(["ffmpeg", "-f", "concat", "-i", ffmpeg_config,
        "-y", "-c", "copy", f"{out_dir}/{OUT_BASE_NAME}.mts"])

def ffmpeg_attach_subs(out_dir):
    video = f"{out_dir}/{OUT_BASE_NAME}.mts"
    subs  = f"{out_dir}/{OUT_BASE_NAME}.srt"
    subprocess.check_output(["ffmpeg", "-i", video, "-vf", f"subtitles={subs}",
        f"{out_dir}/{OUT_BASE_NAME}_with_subs.mts"])

def concat_all(out_files, out_dir):
    ffmpeg_config = gen_ffmpeg_config_file(out_files, out_dir)
    ffmpeg_concat(ffmpeg_config, out_dir)

def seconds2france(seconds):
    """
    Convert float value of seconds to timecode format used is
    hours:minutes:seconds,milliseconds with time units fixed to two zero-padded
    digits and fractions fixed to three zero-padded digits (00:00:00,000). The
    fractional separator used is the comma, since the program was written in
    France.
    """
    hours, rem = divmod(seconds, 3600)
    minutes, sec = divmod(rem, 60)
    int_sec = int(sec)
    return "{:0>2}:{:0>2}:{:0>2},{:0>3}".format(int(hours), int(minutes),
            int_sec, int((sec - int_sec) * 1000))

def generate_subs(tiktoks, out_dir, transition_duration):
    """
    Generate subtitles file in srt format(https://en.wikipedia.org/wiki/SubRip)
    """
    subs_file = f"{out_dir}/{OUT_BASE_NAME}.srt"

    with open(subs_file, "w") as fd:
        current_time = 0.0
        for n, tt in enumerate(tiktoks, 1):
            if not tt.description:
                current_time += tt.duration + transition_duration
                continue
            # A numeric counter indicating the number or position of the
            # subtitle
            fd.write(f"{n}\n")
            # The time that the subtitle should appear on the screen, followed
            # by --> and the time it should disappear
            start_time = seconds2france(current_time)
            end_time = seconds2france(current_time + tt.duration)
            fd.write(f"{start_time} --> {end_time}\n")
            # Subtitle text itself on one or more lines
            fd.write(f"{tt.description.strip()}\n")
            # A blank line containing no text, indicating the end of this
            # subtitle
            fd.write("\n")

            current_time += tt.duration + transition_duration


def main(config):
    # tiktoks = [TikTok.from_url(url) for url in get_urls_from_list(config.input)]
    tiktoks = list(parse_file(config.input))
    download_dir = config.output
    transition = None

    if config.transition is not None:
        transition = os.path.join(download_dir,
                os.path.basename(config.transition))
        shutil.copyfile(config.transition, transition)

    print(f"Number of tik-toks: {len(tiktoks)}")
    print("Downloading...")
    completed_tiktoks = []

    for tt in tiktoks:
        try:
            mp4 = tt.download(download_dir)
            # convert all to mts format to concatenate it later without any problems,
            # XXX: not sure this is the best way to do this:
            # https://video.stackexchange.com/questions/15468/non-monotonous-dts-on-concat-ffmpeg
            mts = ffmpeg_convert_to_mts(mp4)
            tt.duration = float(ffmpeg_format_info(mts)["format"]["duration"])
            print(f"{tt.tid}({tt.duration})done")
            tt.local_file = mts
            completed_tiktoks.append(tt)
        except:
            print(f"{tt.tid} fail")

    out_files = [tt.local_file for tt in completed_tiktoks]

    # insert transition between tt if exist
    if transition is not None:
        transition = ffmpeg_convert_to_mts(transition)
        out_files = intersperse(out_files, transition)
        transition_info = ffmpeg_format_info(transition)
        transition_duration = float(transition_info["format"]["duration"])
    else:
        transition_duration = 0.0

    print("generating full video...")
    concat_all(out_files, download_dir)

    print("generating subs...")
    generate_subs(completed_tiktoks, download_dir, transition_duration)
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
