from .base import BaseAugmentor
from .artmodel.rawnet2 import ArtRawnet2
from .artmodel.btse import ArtBTSE
from .artmodel.aasist_ssl import ArtAasistSSL
from .artmodel.lcnn import ArtLCNN
from .utils import librosa_to_pydub

from art.attacks.evasion import (
    ProjectedGradientDescent,
    FastGradientMethod,
    AutoProjectedGradientDescent,
)

import numpy as np

SUPPORTED_CM = ["rawnet2", "btse", "aasistssl", "lcnn"]
SUPPORTED_ADV = [
    "ProjectedGradientDescent",
    "FastGradientMethod",
    "AutoProjectedGradientDescent",
]

import logging

logger = logging.getLogger(__name__)


class AdversarialNoiseAugmentor(BaseAugmentor):
    """
    Adversarial noise augmentor.

    This augmentor adds adversarial noise to the input audio.
    The adversarial noise is generated by several attacks supported by ART evasion attacks:
    https://adversarial-robustness-toolbox.readthedocs.io/en/latest/index.html

    configs:
    :model_name: name of the classifier (CM) model. Supported models: ${SUPPORTED_CM}
    :model_pretrained: path to the pretrained CM model
    :config_path: path to the configuration file of the CM model
    :device: device to run the CM model (cpu or cuda)
    :adv_method: name of the adversarial methods - supported by ART evasion attacks. Currently supported methods: ${SUPPORTED_ADV}
    :adv_config: configuration of the adversarial method
    """.format(SUPPORTED_CM=SUPPORTED_CM, SUPPORTED_ADV=SUPPORTED_ADV)

    def __init__(self, config: dict, y_true: bool = None):
        """
        This method initializes the `AdversarialNoiseAugmentor` object.

        :param config: configuration of the augmentor
        """
        super().__init__(config)
        self.model_name = config["model_name"]
        self.model_pretrained = config["model_pretrained"]
        self.device = config["device"]
        self.adv_method = config["adv_method"]
        self.y_true = y_true
        # load model
        assert self.model_name in SUPPORTED_CM, "model_name must be one of {}".format(
            SUPPORTED_CM
        )
        if self.model_name == "rawnet2":
            self.artmodel = ArtRawnet2(
                config_path=config["config_path"], device=self.device
            )
            self.artmodel.load_model(self.model_pretrained)
        
        if self.model_name == "btse":
            self.artmodel = ArtBTSE(
                config_path=config["config_path"], device=self.device
            )
            self.artmodel.load_model(self.model_pretrained)
        
        if self.model_name == "aasistssl":
            self.artmodel = ArtAasistSSL(
                ssl_model=config["ssl_model"], device=self.device
            )
            self.artmodel.load_model(self.model_pretrained)

        if self.model_name == "lcnn":
            self.artmodel = ArtLCNN(
                config_path=config["config_path"], device=self.device
            )
            self.artmodel.load_model(self.model_pretrained)
        # load adversarial class
        assert self.adv_method in SUPPORTED_ADV, "adv_method must be one of {}".format(
            SUPPORTED_ADV
        )
        self.adv_class = globals()[self.adv_method](
            self.artmodel.get_art(), **config["adv_config"]
        )
        
    def transform(self):
        # get classifier_art
        classifier_art = self.artmodel.get_art()

        # chunk audio
        chunks, last_size = self.artmodel.get_chunk(self.data)
        
        # list of np.ndarray, contains adversarial noise
        adv_res = []

        for chunk in chunks:
            if self.y_true is not None:
                temp = self.adv_class.generate(x=chunk.cpu().numpy(), y=self.y_true)[0, :]
            temp = self.adv_class.generate(x=chunk.cpu().numpy())[0, :]
            adv_res.append(temp)

        # recover to original length audio
        audio = self.artmodel.chunk_to_audio(adv_res, last_size)
        
        # convert to pydub
        self.augmented_audio = librosa_to_pydub(audio, sr=self.sr)
    
    def transform_load(self, input_dir, batch_size):
        # get classifier_art
        # [TODO] load model here
        raise NotImplementedError