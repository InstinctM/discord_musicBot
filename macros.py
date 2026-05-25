import shutil
node_path = shutil.which("node")

PREFIX = ";"

YTDL_OPTIONS = {
    "format": "bestaudio/best",
    "extractaudio": True,
    "audioformat": "opus", # Discord's native codec
    "outtmpl": "%(extractor)s-%(id)s-%(title)s-%(qhash)s.%(ext)s",
    "restrictfilenames": True,
    "noplaylist": True,
    "nocheckcertificate": True,
    "ignoreerrors": False,
    "logtostderr": False,
    "quiet": True,
    "no_warnings": True,
    "default_search": "auto",
    "source_address": "0.0.0.0", # Prevents IPv6 issues
    "js_runtime": node_path
}

FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': (
        '-vn '                   # No video
        '-acodec libopus '       # Use Opus codec
        '-b:a 128k '             # Set bitrate to 128k (standard high quality for Discord)
        '-vbr on '               # Variable Bitrate for better efficiency
        '-compression_level 10 ' # Highest CPU effort for best quality
        '-filter:a "volume=1.0"' # Keep volume at baseline
    )
}