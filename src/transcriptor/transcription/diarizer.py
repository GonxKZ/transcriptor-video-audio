"""
Speaker diarization module using pyannote.audio for "who spoke when" detection.
"""
import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

try:
    from pyannote.audio import Pipeline
    from pyannote.core import Segment, Timeline
    PYANNOTE_AVAILABLE = True
except ImportError:
    PYANNOTE_AVAILABLE = False
    Pipeline = None
    Segment = None
    Timeline = None

logger = logging.getLogger(__name__)

@dataclass
class DiarizationSegment:
    """Represents a speaker diarization segment."""
    start: float
    end: float
    speaker: str

class PyannoteDiarizer:
    """
    Speaker diarization using pyannote.audio.
    
    Diarization identifies "who spoke when" in an audio recording,
    assigning speaker labels to temporal segments. pyannote.audio
    offers state-of-the-art pipelines in PyTorch.
    
    Note: Recent versions may require Hugging Face token acceptance
    for model access. Users can configure credentials if needed.
    """
    
    def __init__(self, 
                 hf_token: Optional[str] = None,
                 device: str = "cuda"):
        """
        Initialize the diarizer.
        
        Args:
            hf_token: Hugging Face token for model access (if required)
            device: Device to use (cuda, cpu)
        """
        if not PYANNOTE_AVAILABLE:
            raise ImportError(
                "pyannote.audio is not installed. "
                "Install it with: pip install pyannote.audio"
            )
            
        self.hf_token = hf_token
        self.device = device
        self.pipeline = None
        self._load_pipeline()
    
    def _load_pipeline(self):
        """Load the diarization pipeline."""
        try:
            logger.info("Loading pyannote diarization pipeline")
            
            # Configure authentication if token provided
            pipeline_args = {}
            if self.hf_token:
                pipeline_args["use_auth_token"] = self.hf_token
                
            # Load pipeline
            self.pipeline = Pipeline.from_pretrained(
                "pyannote/speaker-diarization-3.1",
                **pipeline_args
            )
            
            # Move to device
            if self.device.startswith("cuda"):
                self.pipeline.to(self.device)
                
            logger.info("pyannote diarization pipeline loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load pyannote diarization pipeline: {e}")
            raise
    
    def diarize(self, 
                audio_path: str,
                num_speakers: Optional[int] = None,
                min_speakers: Optional[int] = None,
                max_speakers: Optional[int] = None) -> Optional[List[DiarizationSegment]]:
        """
        Perform speaker diarization on an audio file.
        
        Args:
            audio_path: Path to the audio file
            num_speakers: Exact number of speakers (if known)
            min_speakers: Minimum number of speakers
            max_speakers: Maximum number of speakers
            
        Returns:
            List of diarization segments with speaker labels, or None if failed
        """
        try:
            logger.info(f"Performing diarization on: {audio_path}")
            
            # Prepare diarization parameters
            diarization_args = {}
            if num_speakers is not None:
                diarization_args["num_speakers"] = num_speakers
            if min_speakers is not None:
                diarization_args["min_speakers"] = min_speakers
            if max_speakers is not None:
                diarization_args["max_speakers"] = max_speakers
                
            # Perform diarization
            diarization = self.pipeline(audio_path, **diarization_args)
            
            # Convert to our format
            segments = []
            for turn, _, speaker in diarization.itertracks(yield_label=True):
                segments.append(DiarizationSegment(
                    start=turn.start,
                    end=turn.end,
                    speaker=speaker
                ))
            
            logger.info(f"Diarization completed with {len(segments)} segments")
            return segments
            
        except Exception as e:
            logger.error(f"Error during diarization: {e}")
            return None
    
    def get_speaker_timeline(self, 
                           audio_path: str,
                           speaker_id: str,
                           num_speakers: Optional[int] = None,
                           min_speakers: Optional[int] = None,
                           max_speakers: Optional[int] = None) -> Optional[Timeline]:
        """
        Get timeline for a specific speaker.
        
        Args:
            audio_path: Path to the audio file
            speaker_id: Speaker identifier to extract timeline for
            num_speakers: Exact number of speakers (if known)
            min_speakers: Minimum number of speakers
            max_speakers: Maximum number of speakers
            
        Returns:
            Timeline for the specified speaker, or None if failed
        """
        try:
            # Perform diarization
            diarization = self.pipeline(
                audio_path,
                num_speakers=num_speakers,
                min_speakers=min_speakers,
                max_speakers=max_speakers
            )
            
            # Extract timeline for specific speaker
            speaker_timeline = diarization.label_timeline(speaker_id)
            return speaker_timeline
            
        except Exception as e:
            logger.error(f"Error getting speaker timeline: {e}")
            return None