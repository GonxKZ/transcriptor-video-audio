"""
Word-level alignment module using WhisperX for precise timing.
"""
import logging
from typing import List, Dict, Optional, Any
import numpy as np

try:
    import whisperx
    WHISPERX_AVAILABLE = True
except ImportError:
    WHISPERX_AVAILABLE = False
    whisperx = None

logger = logging.getLogger(__name__)

class WhisperXAligner:
    """
    Word-level alignment using WhisperX for precise timing.
    
    WhisperX adds a word alignment step with wav2vec2-style models to obtain
    stable per-word timestamps, crucial for professional subtitles and
    synchronization with editors.
    """
    
    def __init__(self, 
                 device: str = "cuda",
                 compute_type: str = "float16",
                 download_root: Optional[str] = None):
        """
        Initialize the aligner.
        
        Args:
            device: Device to use (cuda, cpu)
            compute_type: Compute type (float16, float32, etc.)
            download_root: Directory to download models to
        """
        if not WHISPERX_AVAILABLE:
            raise ImportError(
                "whisperx is not installed. "
                "Install it with: pip install whisperx"
            )
            
        self.device = device
        self.compute_type = compute_type
        self.download_root = download_root
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """Load the alignment model."""
        try:
            logger.info(f"Loading WhisperX alignment model on {self.device}")
            
            # Load alignment model
            self.model = whisperx.load_align_model(
                language_code="en",  # Will be updated per language
                device=self.device,
                download_root=self.download_root
            )
            
            logger.info("WhisperX alignment model loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load WhisperX alignment model: {e}")
            raise
    
    def align_words(self, 
                    segments: List[Dict[str, Any]], 
                    audio_path: str,
                    language: str = "en") -> Optional[List[Dict[str, Any]]]:
        """
        Align word timings for transcription segments.
        
        Args:
            segments: Transcription segments from Whisper
            audio_path: Path to the audio file
            language: Language code
            
        Returns:
            Aligned segments with precise word timings, or None if failed
        """
        try:
            logger.info("Starting word alignment with WhisperX")
            
            # Load audio
            audio = whisperx.load_audio(audio_path)
            
            # Update model if language changed
            if self.model.get("language") != language:
                logger.info(f"Updating alignment model for language: {language}")
                self.model = whisperx.load_align_model(
                    language_code=language,
                    device=self.device,
                    download_root=self.download_root
                )
            
            # Perform alignment
            result = whisperx.align(
                segments,
                self.model,
                audio,
                device=self.device,
                return_char_alignments=False
            )
            
            logger.info("Word alignment completed successfully")
            return result["segments"]
            
        except Exception as e:
            logger.error(f"Error during word alignment: {e}")
            return None
    
    def refine_timestamps(self, 
                         segments: List[Dict[str, Any]], 
                         audio_path: str,
                         language: str = "en") -> Optional[List[Dict[str, Any]]]:
        """
        Refine timestamps with improved accuracy.
        
        Args:
            segments: Transcription segments
            audio_path: Path to the audio file
            language: Language code
            
        Returns:
            Segments with refined timestamps, or None if failed
        """
        # For now, this is the same as align_words
        # In a more advanced implementation, we might add additional refinement steps
        return self.align_words(segments, audio_path, language)