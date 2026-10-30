# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from ..._models import BaseModel
from .audio_transcription import AudioTranscription
from .noise_reduction_type import NoiseReductionType
from .realtime_audio_formats import RealtimeAudioFormats
from .realtime_audio_input_turn_detection import RealtimeAudioInputTurnDetection

class NoiseReduction(BaseModel):
    """Configuration for input audio noise reduction.

    This can be set to `null` to turn off.
    Noise reduction filters audio added to the input audio buffer before it is sent to VAD and the model.
    Filtering the audio can improve VAD and turn detection accuracy (reducing false positives) and model performance by improving perception of the input audio.
    """
    type: Optional[NoiseReductionType] = None

class RealtimeAudioConfigInput(BaseModel):
    format: Optional[RealtimeAudioFormats] = None
    noise_reduction: Optional[NoiseReduction] = None
    transcription: Optional[AudioTranscription] = None
    turn_detection: Optional[RealtimeAudioInputTurnDetection] = None
