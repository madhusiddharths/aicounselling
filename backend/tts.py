
import os
import base64
from google.cloud import texttospeech

def synthesize_text(text: str) -> str:
    """
    Synthesizes speech from the input string of text.
    Returns the Audio Content as a Base64 encoded string.
    """
    client = texttospeech.TextToSpeechClient()

    input_text = texttospeech.SynthesisInput(text=text)

    # Note: Using a "Journey" voice or similar premium voice if available, 
    # otherwise falling back to a standard Wavenet voice. 
    # 'en-US-Journey-F' is a good conversational voice if enabled in your project,
    # otherwise 'en-US-Neural2-F' or 'en-US-Wavenet-F'.
    # Let's use a standard Wavenet voice for high compatibility.
    voice = texttospeech.VoiceSelectionParams(
        language_code="en-US",
        name="en-US-Journey-F" # Trying Journey for better quality
    )

    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3
    )

    try:
        response = client.synthesize_speech(
            request={"input": input_text, "voice": voice, "audio_config": audio_config}
        )
    except Exception as e:
        # Fallback if Journey/Validation fails
        print(f"TTS Error (Journey), falling back to Wavenet: {e}")
        voice = texttospeech.VoiceSelectionParams(
            language_code="en-US",
            name="en-US-Wavenet-F"
        )
        response = client.synthesize_speech(
            request={"input": input_text, "voice": voice, "audio_config": audio_config}
        )

    # Convert to base64 for JSON embedding
    audio_b64 = base64.b64encode(response.audio_content).decode('utf-8')
    return audio_b64
