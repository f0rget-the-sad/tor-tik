# tor-tik

Download tic-toc videos and merge them into one video

## Requiremets
- [TikTokApi](https://dteather.com/TikTok-Api/docs/TikTokApi.html)
- ffmpeg


## Usage Examples

```console
$ ./tor-tik.py --help

 ______   ___   ____                  ______  ____  __  _
|      T /   \ |    \                |      Tl    j|  l/ ]
|      |Y     Y|  D  )     _____     |      | |  T |  ' /
l_j  l_j|  O  ||    /     |     |    l_j  l_j |  | |    \
  |  |  |     ||    \     l_____j      |  |   |  | |     Y
  |  |  l     !|  .  Y                 |  |   j  l |  .  |
  l__j   \___/ l__j\_j                 l__j  |____jl__j\_j

usage: tor-tik.py [-h] -i INPUT -o OUTPUT [-t TRANSITION]

optional arguments:
  -h, --help            show this help message and exit
  -i INPUT, --input INPUT
                        Input list file of tic-toks
  -o OUTPUT, --output OUTPUT
                        Output directory, where will stored all the results
  -t TRANSITION, --transition TRANSITION
                        Transition video(will be inserted after each tic-tok)

$ ./tor-tik.py -i tt_list_example.txt -o downloads
```

## Links
- https://medium.com/analytics-vidhya/download-tiktoks-with-python-dcbd79a5237f
- http://www.patorjk.com/software/taag/#p=display&f=Crawford&t=tor%20-%20tik

## TODO
- [x] Download tt videos from list
- [x] Merge them together
- [x] Insert some short transition between them
- [ ] Replace text smiles with rendered one(or render text + smiles and put on
  top of video)
- [ ] Generate some sort of time codes(separate or bake into a video) - to be
  able to know what is the link of the tiktok currently playing
- [ ] Copy from TikTok messages is fucking mess, if you just C-C it's in
  reversed order, but multi-line comments are ok, they are passed in protobuf no
  idea how to parse
