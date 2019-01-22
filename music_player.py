from mutagen.mp3 import MP3
from pygame import mixer
from time import sleep
from threading import Thread
import requests
from PyQt5.QtCore import QThread, pyqtSignal

class MusicPlayer(QThread):
    on_title_change = pyqtSignal(str)
    on_queue_empty = pyqtSignal(bool)
    on_queue_size_change = pyqtSignal(int)

    def __init__(self):
        QThread.__init__(self)
        mixer.init()
        self.is_now_playing = None
        self.queue = []
        self.current_playing_length = 0
        self.current_playing_title = ''


    def __del__(self):
        self.wait()
        

    def add_in_queue(self, path, title=None):
        print('ADD IN QUEUE: {}'.format(path))
        self.queue.append({ 'path': path, 'title': title })
        self.on_queue_size_change.emit(len(self.queue))


    def play_next_song_from_queue(self):
        if len(self.queue) > 0:
            song = self.queue.pop()
            self.on_queue_size_change.emit(len(self.queue))
            path = song['path']
            title = song['title']
            
            print('Playing: {}'.format(path))

            mixer.music.load(path)
            mixer.music.play()
            self.is_now_playing = True
            self.current_playing_title = title
            self.current_playing_length = MP3(path).info.length
        else:
            self.is_now_playing = False
            self.current_playing_title = 'Nothing is playing...'
            self.current_playing_length = 0
            self.on_queue_empty.emit(True)

        self.on_title_change.emit(self.current_playing_title)


    def is_playing(self):
        try:
            if mixer.music.get_busy() == 1:
                return True
            return False
        except:
            return False


    def is_paused(self):
        if self.is_playing() and self.is_now_playing is False:
            return True
        return False


    def play(self):
        if self.is_playing() and self.is_paused() is False:
            return

        try:
            if self.is_paused():
                mixer.music.unpause()
            else:
                mixer.music.play()
        except Exception as e:
            self.play_next_song_from_queue()
        
        self.is_now_playing = True

    
    def pause(self):
        if self.is_playing():
            self.is_now_playing = False
            mixer.music.pause()

    
    def get_song_time(self): 
        if self.is_playing():
            return { 'current': mixer.music.get_pos() / 1000, 'end': self.current_playing_length }
        return None


    def get_time_until_finish(self):
        if self.is_playing():
            return self.current_playing_length - mixer.music.get_pos() / 1000
        return -1

    
    def get_queue_size(self):
        return len(self.queue)

    def run(self):
        while True:
            if self.is_playing() == False and self.is_now_playing:
                self.play_next_song_from_queue()
            sleep(1)
