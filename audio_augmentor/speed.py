from .base import BaseAugmentor
from .utils import librosa_to_pydub
from pydub import AudioSegment
import random


class SpeedAugmentor(BaseAugmentor):
    def __init__(self, input_path, config):
        """
        Speed augmentor class requires these config:
        min_speed_factor: float, min speed factor
        max_speed_factor: float, max speed factor
        """
        super().__init__(input_path, config)
        self.speed_factor = random.uniform(config["min_speed_factor"], config["max_speed_factor"])
        
        self.audio_data = None
        
    def load(self):
        # load with librosa
        super().load()
        # transform to pydub audio segment
        self.audio_data = librosa_to_pydub(self.data, sr=self.sr)
        
    def transform(self):
        self.augmented_audio = self.audio_data.speedup(self.speed_factor)