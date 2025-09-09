"""
Transcription module using faster-whisper for high-fidelity speech recognition.
"""
import os
import logging
from typing import List, Dict, Optional, Iterator
from dataclasses import dataclass
from enum import Enum

try:
    from faster_whisper import WhisperModel
    FASTER_WHISPER_AVAILABLE = True
except ImportError:
    FASTER_WHISPER_AVAILABLE = False
    WhisperModel = None

logger = logging.getLogger(__name__)

class ModelSize(Enum):
    """Whisper model sizes."""
    TINY = "tiny"
    BASE = "base"
    SMALL = "small"
    MEDIUM = "medium"
    LARGE_V1 = "large-v1"
    LARGE_V2 = "large-v2"
    LARGE_V3 = "large-v3"

@dataclass
class TranscriptionSegment:
    """Represents a transcribed segment."""
    id: int
    seek: int
    start: float
    end: float
    text: str
    tokens: List[int]
    temperature: float
    avg_logprob: float
    compression_ratio: float
    no_speech_prob: float
    words: Optional[List[Dict]] = None  # Word-level timing if available

@dataclass
class TranscriptionResult:
    """Complete transcription result."""
    segments: List[TranscriptionSegment]
    language: str
    language_probability: float

class FasterWhisperTranscriber:
    """
    High-fidelity transcription using faster-whisper (CTranslate2 implementation).
    
    faster-whisper packages Whisper over CTranslate2 for significantly
    faster and more memory-efficient inference, supporting int8/int16
    quantization and execution on CPU or CUDA.
    """
    
    def __init__(self, 
                 model_size: str = "large-v3",
                 device: str = "cuda",
                 compute_type: str = "float16",
                 download_root: Optional[str] = None):
        """
        Initialize the transcriber.
        
        Args:
            model_size: Model size (tiny, base, small, medium, large-v3)
            device: Device to use (cuda, cpu)
            compute_type: Compute type (float16, int8, int16, etc.)
            download_root: Directory to download models to
        """
        if not FASTER_WHISPER_AVAILABLE:
            raise ImportError(
                "faster-whisper is not installed. "
                "Install it with: pip install faster-whisper"
            )
            
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self.download_root = download_root
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """Load the Whisper model."""
        try:
            logger.info(f"Loading Whisper model: {self.model_size} on {self.device}")
            
            model_args = {
                "model_size_or_path": self.model_size,
                "device": self.device,
                "compute_type": self.compute_type
            }
            
            if self.download_root:
                model_args["download_root"] = self.download_root
                
            self.model = WhisperModel(**model_args)
            logger.info("Whisper model loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {e}")
            raise
    
    def transcribe(self, 
                   audio_path: str,
                   language: Optional[str] = None,
                   task: str = "transcribe",
                   beam_size: int = 5,
                   temperature: float = 0.0,
                   vad_filter: bool = True,
                   **kwargs) -> Optional[TranscriptionResult]:
        """
        Transcribe an audio file.
        
        Args:
            audio_path: Path to the audio file (16kHz mono WAV recommended)
            language: Language code (None for auto-detection)
            task: Task type ("transcribe" or "translate")
            beam_size: Beam size for decoding
            temperature: Temperature for sampling
            vad_filter: Whether to apply VAD filter
            **kwargs: Additional arguments for the transcriber
            
        Returns:
            Transcription result or None if failed
        """
        if not os.path.exists(audio_path):
            logger.error(f"Audio file not found: {audio_path}")
            return None
            
        try:
            logger.info(f"Transcribing: {audio_path}")
            
            # Prepare transcription parameters
            transcribe_args = {
                "language": language,
                "task": task,
                "beam_size": beam_size,
                "temperature": temperature,
                "vad_filter": vad_filter,
                **kwargs
            }
            
            # Perform transcription
            segments, info = self.model.transcribe(audio_path, **transcribe_args)
            
            # Convert segments to our format
            transcription_segments = []
            for i, segment in enumerate(segments):
                # Convert word timings if available
                words = None
                if hasattr(segment, 'words') and segment.words:
                    words = [
                        {
                            "start": word.start,
                            "end": word.end,
                            "word": word.word,
                            "probability": word.probability
                        }
                        for word in segment.words
                    ]
                
                transcription_segments.append(TranscriptionSegment(
                    id=segment.id,
                    seek=segment.seek,
                    start=segment.start,
                    end=segment.end,
                    text=segment.text,
                    tokens=segment.tokens,
                    temperature=segment.temperature,
                    avg_logprob=segment.avg_logprob,
                    compression_ratio=segment.compression_ratio,
                    no_speech_prob=segment.no_speech_prob,
                    words=words
                ))
            
            result = TranscriptionResult(
                segments=transcription_segments,
                language=info.language,
                language_probability=info.language_probability
            )
            
            logger.info(f"Transcription completed. Detected language: {info.language}")
            return result
            
        except Exception as e:
            logger.error(f"Error during transcription: {e}")
            return None
    
    def transcribe_stream(self, 
                         audio_path: str,
                         language: Optional[str] = None,
                         task: str = "transcribe",
                         beam_size: int = 5,
                         temperature: float = 0.0,
                         **kwargs) -> Iterator[TranscriptionSegment]:
        """
        Transcribe an audio file and yield segments as they become available.
        
        Args:
            audio_path: Path to the audio file (16kHz mono WAV recommended)
            language: Language code (None for auto-detection)
            task: Task type ("transcribe" or "translate")
            beam_size: Beam size for decoding
            temperature: Temperature for sampling
            **kwargs: Additional arguments for the transcriber
            
        Yields:
            Transcription segments as they are processed
        """
        if not os.path.exists(audio_path):
            logger.error(f"Audio file not found: {audio_path}")
            return
            
        try:
            logger.info(f"Streaming transcription: {audio_path}")
            
            # Prepare transcription parameters
            transcribe_args = {
                "language": language,
                "task": task,
                "beam_size": beam_size,
                "temperature": temperature,
                **kwargs
            }
            
            # Perform streaming transcription
            segments, info = self.model.transcribe(audio_path, **transcribe_args)
            
            logger.info(f"Streaming transcription started. Detected language: {info.language}")
            
            for segment in segments:
                # Convert word timings if available
                words = None
                if hasattr(segment, 'words') and segment.words:
                    words = [
                        {
                            "start": word.start,
                            "end": word.end,
                            "word": word.word,
                            "probability": word.probability
                        }
                        for word in segment.words
                    ]
                
                yield TranscriptionSegment(
                    id=segment.id,
                    seek=segment.seek,
                    start=segment.start,
                    end=segment.end,
                    text=segment.text,
                    tokens=segment.tokens,
                    temperature=segment.temperature,
                    avg_logprob=segment.avg_logprob,
                    compression_ratio=segment.compression_ratio,
                    no_speech_prob=segment.no_speech_prob,
                    words=words
                )
                
        except Exception as e:
            logger.error(f"Error during streaming transcription: {e}")