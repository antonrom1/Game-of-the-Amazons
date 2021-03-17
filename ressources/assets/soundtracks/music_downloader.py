import pafy
from pydub import AudioSegment
import os

def download(url):
    video = pafy.new(url)
    best_audio = video.getbestaudio()

    filename = video.title + "." + best_audio.extension
    best_audio.download(filename)

    return filename


def to_mp3(filename):
    AudioSegment.from_file(filename).export(".".join(filename.split(".")[:-1]) + ".mp3", format='mp3')
    os.remove(filename)


def download_playlist_mp3(playlist_url):
    for url in list(pafy.get_playlist(playlist_url)[:10]):
        to_mp3(download(url))


to_mp3(download(input()))