import ffmpeg
import os
import torch
import torchaudio

def extract_audio(input_path: str, output_dir: str) -> str | None:
    """
    Extracts audio from a media file, converts it to 16kHz mono WAV.

    Args:
        input_path: Path to the input media file.
        output_dir: Directory to save the processed WAV file.

    Returns:
        The path to the extracted WAV file, or None if an error occurred.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    base_name = os.path.splitext(os.path.basename(input_path))[0]
    output_path = os.path.join(output_dir, f"{base_name}_processed.wav")

    print(f"Extracting audio from '{input_path}'")
    print(f"Output will be saved to '{output_path}'")

    try:
        # Probe the file to see if it has an audio stream
        probe = ffmpeg.probe(input_path)
        audio_streams = [s for s in probe['streams'] if s['codec_type'] == 'audio']
        if not audio_streams:
            print(f"Error: No audio stream found in '{input_path}'")
            return None

        stream = ffmpeg.input(input_path)
        
        # Convert to 16kHz mono PCM
        stream = ffmpeg.output(stream.audio, output_path, ac=1, ar=16000, acodec='pcm_s16le')
        
        # Overwrite output file if it exists
        ffmpeg.run(stream, overwrite_output=True, quiet=True)

        print("Audio extraction successful.")
        return output_path
    except ffmpeg.Error as e:
        print("FFmpeg Error:", e.stderr.decode() if e.stderr else "Unknown error")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None

def segment_audio_with_vad(audio_path: str):
    """
    Uses Silero VAD to find speech segments in an audio file.

    Args:
        audio_path: Path to the WAV audio file (16kHz mono).

    Returns:
        A list of dicts with 'start' and 'end' timestamps in samples.
    """
    print("Starting VAD segmentation...")
    try:
        model, utils = torch.hub.load(repo_or_dir='snakers4/silero-vad',
                                      model='silero_vad',
                                      force_reload=False)

        (get_speech_timestamps,
         _, _, _, _) = utils

        # Silero VAD works with 16000Hz mono audio
        wav, sr = torchaudio.load(audio_path)
        if sr != 16000:
            resampler = torchaudio.transforms.Resample(sr, 16000)
            wav = resampler(wav)
        
        if wav.shape[0] > 1:
            wav = torch.mean(wav, dim=0, keepdim=True)

        speech_timestamps = get_speech_timestamps(wav, model, sampling_rate=16000)
        print(f"VAD found {len(speech_timestamps)} speech segments.")
        return speech_timestamps
    except Exception as e:
        print(f"An error occurred during VAD segmentation: {e}")
        return None
