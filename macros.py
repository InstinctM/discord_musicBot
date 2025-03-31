PREFIX = ";"

YTDL_OPTIONS = {"format": "bestaudio/best", "outtmpl": "%(extractor)s-%(id)s-%(title)s-%(qhash)s.%(ext)s", "quiet": True}
FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5','options': '-vn -filter:a "volume=1.0"'}