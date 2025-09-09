"""
Voice Activity Detection (VAD) module using Silero VAD.
"""
import torch
import torchaudio
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class SileroVAD:
    """
    Voice Activity Detection using Silero VAD model.
    
    VAD (Voice Activity Detection) detects speech regions in audio,
    helping to segment audio into meaningful chunks for transcription.
    """
    
    def __init__(self, model_url: Optional[str] = None):
        """
        Initialize Silero VAD.
        
        Args:
            model_url: Optional custom model URL
        """
        self.model = None
        self.utils = None
        self.model_url = model_url
        self._load_model()
    
    def _load_model(self):
        """Load the Silero VAD model."""
        try:
            if self.model_url:
                self.model, self.utils = torch.hub.load(
                    repo_or_dir=self.model_url,
                    model='silero_vad',
                    force_reload=False
                )
            else:
                self.model, self.utils = torch.hub.load(
                    repo_or_dir='snakers4/silero-vad',
                    model='silero_vad',
                    force_reload=False
                )
                
            logger.info("Silero VAD model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load Silero VAD model: {e}")
            raise
    
    def detect_speech(self, audio_path: str, 
                     threshold: float = 0.5,
                     min_speech_duration: float = 0.5,
                     min_silence_duration: float = 0.5) -> Optional[List[Dict]]:
        """
        Detect speech segments in an audio file.
        
        Args:
            audio_path: Path to the WAV audio file (16kHz mono)
            threshold: Speech probability threshold (0.0-1.0)
            min_speech_duration: Minimum speech duration in seconds
            min_silence_duration: Minimum silence duration in seconds
            
        Returns:
            List of speech segments with 'start' and 'end' timestamps in seconds,
            or None if failed
        """
        try:
            # Load audio file
            wav, sr = torchaudio.load(audio_path)
            
            # Resample to 16kHz if needed
            if sr != 16000:
                resampler = torchaudio.transforms.Resample(sr, 16000)
                wav = resampler(wav)
            
            # Convert to mono if needed
            if wav.shape[0] > 1:
                wav = torch.mean(wav, dim=0, keepdim=True)
            
            # Get speech timestamps function from utils
            get_speech_timestamps = self.utils[0]
            
            # Detect speech segments
            speech_timestamps = get_speech_timestamps(
                wav,
                self.model,
                sampling_rate=16000,
                threshold=threshold,
                min_speech_duration_ms=int(min_speech_duration * 1000),
                min_silence_duration_ms=int(min_silence_duration * 1000)
            )
            
            # Convert timestamps from samples to seconds
            segments = []
            for segment in speech_timestamps:
                segments.append({
                    'start': segment['start'] / 16000.0,
                    'end': segment['end'] / 16000.0
                })
            
            logger.info(f"Detected {len(segments)} speech segments")
            return segments
            
        except Exception as e:
            logger.error(f"Error during VAD processing: {e}")
            return None
    
    def segment_audio(self, audio_path: str, 
                     output_dir: str,
                     threshold: float = 0.5,
                     min_speech_duration: float = 0.5,
                     min_silence_duration: float = 0.5,
                     margin: float = 0.2) -> Optional[List[str]]:
        """
        Segment audio file into individual speech segments.
        
        Args:
            audio_path: Path to the WAV audio file (16kHz mono)
            output_dir: Directory to save segmented audio files
            threshold: Speech probability threshold (0.0-1.0)
            min_speech_duration: Minimum speech duration in seconds
            min_silence_duration: Minimum silence duration in seconds
            margin: Additional margin (in seconds) to add to each segment
            
        Returns:
            List of paths to segmented audio files, or None if failed
        """
        import os
        import soundfile as sf
        
        # Detect speech segments
        segments = self.detect_speech(
            audio_path, threshold, min_speech_duration, min_silence_duration
        )
        
        if segments is None:
            return None
            
        if not segments:
            logger.warning("No speech segments detected")
            return []
            
        # Load full audio
        audio_data, sample_rate = sf.read(audio_path)
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Segment audio
        segment_paths = []
        for i, segment in enumerate(segments):
            # Calculate sample indices with margin
            start_sample = max(0, int((segment['start'] - margin) * sample_rate))
            end_sample = min(len(audio_data), int((segment['end'] + margin) * sample_rate))
            
            # Extract segment
            segment_data = audio_data[start_sample:end_sample]
            
            # Save segment
            segment_path = os.path.join(output_dir, f"segment_{i:04d}.wav")
            sf.write(segment_path, segment_data, sample_rate)
            segment_paths.append(segment_path)
            
        logger.info(f"Segmented audio into {len(segment_paths)} files")
        return segment_paths