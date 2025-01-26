from melo.api import TTS
from django.conf import settings
import datetime
import whisper

device = "auto"


tts_model = None
whisper_model = None


def tts(text, speed=1.0):
    global tts_model
    if tts_model is None:
        tts_model = TTS(language="EN_V2", device=device)

    speaker_ids = tts_model.hps.data.spk2id

    output_path = f"tts_{int(datetime.datetime.now().timestamp())}.wav"

    tts_model.tts_to_file(text, speaker_ids["EN-BR"], output_path, speed=speed)

    return output_path


def transcribe(path):
    global whisper_model
    if whisper_model is None:
        whisper_model = whisper.load_model("medium")

    result = whisper_model.transcribe(path, word_timestamps=True)
    segments = result["segments"]

    if not segments:
        raise ValueError("something went wrong ;(")

    words = list(
        map(
            lambda x: (x["word"].strip(), x["start"], x["end"]),
            [word for segment in segments for word in segment["words"]],
        )
    )

    return words


def get_transcribed_tts(text, speed=1.0):
    audio_path = tts(text, speed)
    transcription = transcribe(audio_path)

    return audio_path, transcription
