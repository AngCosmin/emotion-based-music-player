from time import sleep
from datetime import datetime, timedelta
from imgurpython import ImgurClient
from helpers import get_config
from PyQt5 import QtWidgets, uic, QtGui
from PyQt5.QtCore import QThread, pyqtSignal
from threading import Thread
from music_player import MusicPlayer
import os
import json
import youtube_dl
import requests
import cv2

app = QtWidgets.QApplication([])
dialog = uic.loadUi('main.ui')
last_emotions = []

player = MusicPlayer()

def authenticate() -> ImgurClient:
    config = get_config()
    config.read('.env')
    client_id = config.get('imgur', 'client_id')
    client_secret = config.get('imgur', 'client_secret')

    return ImgurClient(client_id, client_secret)


def upload(client: ImgurClient):
    config = {
        'album': None,
        'name': 'EmotionAnalyzer!',
        'title': 'EmotionAnalyzer!',
    }

    print("Uploading image... ")
    image = client.upload_from_path('you.png', config=config, anon=False)
    print("Done\n")

    return image


def analyze(image_link: str) -> (str, None):
    config = get_config()
    config.read('.env')
    api_key = config.get('microsoft', 'api_key')

    url = 'https://westeurope.api.cognitive.microsoft.com/face/v1.0/detect?returnFaceId=true&returnFaceLandmarks=false&returnFaceAttributes=emotion'

    headers = {
        'content-type': 'application/json',
        'Ocp-Apim-Subscription-Key': api_key,
    }

    response = requests.post(url, data=json.dumps({'url': image_link}), headers=headers)
    response = json.loads(response.text)

    if len(response) == 0:
        return None
    else:
        emotion = response[0]['faceAttributes']['emotion']
        return max(emotion, key=emotion.get)


def take_photo(camera):
    print('Taking photo...')
    ret, frame = camera.read()  # return a single frame in variable `frame`
    cv2.imwrite('you.png', frame)


def on_download(params):
    if params['status'] == 'downloading':
        print('[Download] {} [{}] [Estimated {}]'.format(params['filename'], params['_percent_str'], params['_eta_str']))
    else:
        print(params)


def download_song(link: str):
    options = {
        'format': 'bestaudio/best',
        'outtmpl': '%(id)s.%(ext)s',
        'nocheckcertificate': True,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '128',
        }],
        'quiet': True,
        'progress_hooks': [on_download]
    }

    if not os.path.exists('songs'):
        os.mkdir('songs')
        os.chdir('songs')
    else:
        os.chdir('songs')

    youtube_downloader = youtube_dl.YoutubeDL(options)

    try:
        video_info = youtube_downloader.extract_info(link, download=True)
        os.chdir('../')
        return {'id': video_info['id'], 'title': video_info['title']}
    except Exception as e:
        print(e)
        os.chdir('../')
        return None

def get_dominant_emotion(emotions: list, last_x_minutes: int) -> str:
    last_minutes = datetime.now() - timedelta(minutes=last_x_minutes)
    dominant_emotions = {
        'anger': 0,
        'contempt': 0,
        'disgust': 0,
        'fear': 0,
        'happiness': 0,
        'sadness': 0,
        'surprise': 0,
        'neutral': 0,
    }

    for item in reversed(emotions):
        if item['datetime'] >= last_minutes:
            if item['emotion'] is not None:
                dominant_emotions[item['emotion']] += 1
        else:
            emotions.remove(item)

    dominant = max(dominant_emotions, key=dominant_emotions.get)
    if dominant is None:
        return None
    else:
        return dominant


def on_play_pause_clicked():
    if player.is_playing() and player.is_paused() is False:
        dialog.buttonPlayPause.setIcon(QtGui.QIcon('icons/play.png'))
        player.pause()
    else:
        dialog.buttonPlayPause.setIcon(QtGui.QIcon('icons/pause.png'))
        player.play()


def on_skip_clicked():
    if player.is_playing() and player.get_queue_size() > 0:
        player.play_next_song_from_queue()


class GUIUpdateEmotion(QThread):
    emotion = pyqtSignal(str)

    def __init__(self, ):
        QThread.__init__(self)

    def __del__(self):
        self.wait()

    def run(self):
        client = authenticate()
        camera = cv2.VideoCapture(0)

        while True:
            print ('Taking photo in 2 seconds')
            sleep(1)
            print ('Taking photo in 1 seconds')
            sleep(1)
            print ('Now')

            # take_photo(camera)
            # image = upload(client)
            emotion = 'happiness'
            print(emotion)
            last_emotions.append({'datetime': datetime.now(), 'emotion': emotion})
            dominant = get_dominant_emotion(last_emotions, 1)
            self.emotion.emit('Last {} / Dominant {}'.format(emotion, dominant))

            if player.get_queue_size() == 0 or 0 <= player.get_time_until_finish() <= 20:
                print ('Getting recommanded song')
                response = requests.post("http://localhost/youtube-api/index.php", params={'username': 'Cosmin', 'password': 'cosmin', 'emotion': dominant}) 
                response = json.loads(response.content.decode('utf-8'))

                print(response)

                if response['success'] == True:
                    url = response['link']
                    song = download_song(url)

                    if song:
                        player.add_in_queue('songs/{}.mp3'.format(song['id']), song['title'])
                    else:
                        print('Could not download song')
                else:
                    print(response['message'])
            else:
                print('Queue is full')

            sleep(5)


class GUIUpdateSongProgress(QThread):
    completed = pyqtSignal(int, str)

    def __init__(self, player: MusicPlayer):
        QThread.__init__(self)
        self.player = player

    def __del__(self):
        self.wait()

    def run(self):
        while True:
            song_time = self.player.get_song_time() 

            if song_time is None:
                self.completed.emit(0, '0:00')
            else:
                current = song_time['current']
                end = song_time['end']

                if end == 0:
                    percent = 0
                else:
                    percent = int(current / end * 100)

                label = '{}/{}'.format(int(current), int(end))
                self.completed.emit(percent, label)

            sleep(0.1)


def update_predominant_emotion(predominant_emotion):
    dialog.labelEmotion.setText(predominant_emotion)


def update_progress_bar(percent, label):
    dialog.progressBar.setValue(percent)
    dialog.progressBar.setFormat(label)


def update_song_title(title):
    dialog.labelSongName.setText(title)


def ui_update_on_queue_empty(is_empty: bool):
    dialog.buttonPlayPause.setIcon(QtGui.QIcon('icons/play.png'))


def ui_update_on_queue_size_change(no_songs_in_queue: int):
    dialog.labelInQueue.setText('In queue: ' + str(no_songs_in_queue) + ' songs')


player.on_title_change.connect(update_song_title)
player.on_queue_empty.connect(ui_update_on_queue_empty)
player.on_queue_size_change.connect(ui_update_on_queue_size_change)
player.start()

t = GUIUpdateSongProgress(player)
t.completed.connect(update_progress_bar)
t.start()

s = GUIUpdateEmotion()
s.emotion.connect(update_predominant_emotion)
s.start()

dialog.buttonPlayPause.clicked.connect(on_play_pause_clicked)
dialog.buttonSkip.clicked.connect(on_skip_clicked)

dialog.show()
app.exec()
