"""
Robust streaming pipeline with fault tolerance for audio processing.
"""
import os
import json
import hashlib
import logging
from typing import List, Dict, Optional, Callable, Any
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
from queue import Queue
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

from ..audio.preprocessor import AudioPreprocessor
from ..audio.vad import SileroVAD
from ..transcription.faster_whisper import FasterWhisperTranscriber
from ..transcription.aligner import WhisperXAligner
from ..transcription.diarizer import PyannoteDiarizer

logger = logging.getLogger(__name__)

class ProcessingStage(Enum):
    """Stages of the processing pipeline."""
    EXTRACT_AUDIO = "extract_audio"
    VAD_SEGMENTATION = "vad_segmentation"
    TRANSCRIPTION = "transcription"
    ALIGNMENT = "alignment"
    DIARIZATION = "diarization"
    MERGE_SEGMENTS = "merge_segments"
    EXPORT = "export"

@dataclass
class ProcessingState:
    """State of a processing task."""
    file_path: str
    stage: ProcessingStage
    status: str  # "pending", "running", "completed", "failed"
    progress: float  # 0.0 to 1.0
    result: Optional[Any] = None
    error: Optional[str] = None
    timestamp: float = 0.0
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "file_path": self.file_path,
            "stage": self.stage.value,
            "status": self.status,
            "progress": self.progress,
            "result": self.result,
            "error": self.error,
            "timestamp": self.timestamp
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "ProcessingState":
        """Create from dictionary."""
        data["stage"] = ProcessingStage(data["stage"])
        return cls(**data)

class StreamingPipeline:
    """
    Robust streaming pipeline with fault tolerance for audio processing.
    
    The pipeline divides work into stages connected by queues:
    1. Ingestion and extraction with FFmpeg
    2. VAD + optional diarization
    3. Transcription with GPU workers
    4. Alignment for word-level timing
    5. Merge and compact segments
    6. Export to various formats
    
    Each stage writes idempotent states to disk so processing can resume
    after interruption without reprocessing.
    """
    
    def __init__(self, 
                 workspace_dir: str,
                 settings: dict,
                 max_workers: int = 4,
                 gpu_devices: List[str] = None):
        """
        Initialize the streaming pipeline.
        
        Args:
            workspace_dir: Directory for temporary files and state tracking
            settings: Dictionary with pipeline settings
            max_workers: Maximum number of concurrent workers
            gpu_devices: List of GPU devices to use (e.g., ["cuda:0", "cuda:1"])
        """
        self.workspace_dir = Path(workspace_dir)
        self.settings = settings
        self.workspace_dir.mkdir(exist_ok=True)
        
        self.max_workers = max_workers
        self.gpu_devices = gpu_devices or ["cuda:0"] if self._has_cuda() else ["cpu"]
        
        # Create subdirectories
        self.temp_dir = self.workspace_dir / "temp"
        self.temp_dir.mkdir(exist_ok=True)
        
        self.states_dir = self.workspace_dir / "states"
        self.states_dir.mkdir(exist_ok=True)
        
        self.segments_dir = self.workspace_dir / "segments"
        self.segments_dir.mkdir(exist_ok=True)
        
        # Initialize components
        self.preprocessor = AudioPreprocessor(str(self.temp_dir))
        self.vad = SileroVAD()
        
        # Thread pools
        self.cpu_executor = ThreadPoolExecutor(max_workers=max_workers)
        self.gpu_executors = {
            device: ThreadPoolExecutor(max_workers=1)  # One worker per GPU to avoid oversubscription
            for device in self.gpu_devices
        }
        
        # Processing queues
        self.extraction_queue = Queue()
        self.vad_queue = Queue()
        self.transcription_queue = Queue()
        self.alignment_queue = Queue()
        self.diarization_queue = Queue()
        self.merge_queue = Queue()
        self.export_queue = Queue()
        
        # Worker threads
        self.workers = []
        
        # Callbacks
        self.progress_callback: Optional[Callable[[ProcessingState], None]] = None
        self.completion_callback: Optional[Callable[[str, Any], None]] = None
        
    def _has_cuda(self) -> bool:
        """Check if CUDA is available."""
        try:
            import torch
            return torch.cuda.is_available()
        except ImportError:
            return False
    
    def set_progress_callback(self, callback: Callable[[ProcessingState], None]):
        """
        Set callback for progress updates.
        
        Args:
            callback: Function to call with ProcessingState updates
        """
        self.progress_callback = callback
    
    def set_completion_callback(self, callback: Callable[[str, Any], None]):
        """
        Set callback for completion notifications.
        
        Args:
            callback: Function to call when processing completes (file_path, result)
        """
        self.completion_callback = callback
    
    def get_state_file_path(self, file_path: str, stage: ProcessingStage) -> Path:
        """
        Get the path to the state file for a given file and stage.
        
        Args:
            file_path: Path to the input file
            stage: Processing stage
            
        Returns:
            Path to the state file
        """
        # Create a hash of the file path and stage
        file_hash = hashlib.md5(f"{file_path}_{stage.value}".encode()).hexdigest()
        return self.states_dir / f"{file_hash}.json"
    
    def save_state(self, state: ProcessingState):
        """
        Save processing state to disk.
        
        Args:
            state: Processing state to save
        """
        state_file = self.get_state_file_path(state.file_path, state.stage)
        try:
            with open(state_file, 'w') as f:
                json.dump(state.to_dict(), f, indent=2)
            logger.debug(f"Saved state for {state.file_path} at stage {state.stage}")
        except Exception as e:
            logger.error(f"Failed to save state for {state.file_path}: {e}")
    
    def load_state(self, file_path: str, stage: ProcessingStage) -> Optional[ProcessingState]:
        """
        Load processing state from disk.
        
        Args:
            file_path: Path to the input file
            stage: Processing stage
            
        Returns:
            Processing state or None if not found
        """
        state_file = self.get_state_file_path(file_path, stage)
        if not state_file.exists():
            return None
            
        try:
            with open(state_file, 'r') as f:
                data = json.load(f)
            state = ProcessingState.from_dict(data)
            logger.debug(f"Loaded state for {file_path} at stage {stage}")
            return state
        except Exception as e:
            logger.error(f"Failed to load state for {file_path}: {e}")
            return None
    
    def start_processing(self, file_path: str):
        """
        Start processing a file.
        
        Args:
            file_path: Path to the input audio/video file
        """
        logger.info(f"Starting processing for {file_path}")
        
        # Create initial state
        state = ProcessingState(
            file_path=file_path,
            stage=ProcessingStage.EXTRACT_AUDIO,
            status="pending",
            progress=0.0,
            timestamp=time.time()
        )
        
        # Save initial state
        self.save_state(state)
        
        # Add to extraction queue
        self.extraction_queue.put(file_path)
    
    def _extraction_worker(self):
        """Worker for audio extraction stage."""
        while True:
            try:
                file_path = self.extraction_queue.get(timeout=1)
                if file_path is None:  # Shutdown signal
                    break
                    
                logger.info(f"Extracting audio from {file_path}")
                
                # Check if we already have a completed state
                state = self.load_state(file_path, ProcessingStage.EXTRACT_AUDIO)
                if state and state.status == "completed":
                    logger.info(f"Skipping extraction for {file_path} (already completed)")
                    self.vad_queue.put(file_path)
                    self.extraction_queue.task_done()
                    continue
                
                # Update state to running
                state = ProcessingState(
                    file_path=file_path,
                    stage=ProcessingStage.EXTRACT_AUDIO,
                    status="running",
                    progress=0.0,
                    timestamp=time.time()
                )
                self.save_state(state)
                if self.progress_callback:
                    self.progress_callback(state)
                
                # Process audio extraction
                processed_path = self.preprocessor.process_audio_pipeline(
                    file_path, 
                    normalize=True, 
                    denoise=False
                )
                
                if processed_path:
                    # Update state to completed
                    state.status = "completed"
                    state.progress = 1.0
                    state.result = processed_path
                    state.timestamp = time.time()
                    self.save_state(state)
                    if self.progress_callback:
                        self.progress_callback(state)
                    
                    # Add to next stage
                    self.vad_queue.put(file_path)
                else:
                    # Update state to failed
                    state.status = "failed"
                    state.error = "Audio extraction failed"
                    state.timestamp = time.time()
                    self.save_state(state)
                    if self.progress_callback:
                        self.progress_callback(state)
                
                self.extraction_queue.task_done()
                
            except Exception as e:
                logger.error(f"Error in extraction worker: {e}")
                # Continue processing other items
    
    def _vad_worker(self):
        """Worker for VAD segmentation stage."""
        while True:
            try:
                file_path = self.vad_queue.get(timeout=1)
                if file_path is None:  # Shutdown signal
                    break
                    
                logger.info(f"Performing VAD segmentation on {file_path}")
                
                # Check if we already have a completed state
                state = self.load_state(file_path, ProcessingStage.VAD_SEGMENTATION)
                if state and state.status == "completed":
                    logger.info(f"Skipping VAD for {file_path} (already completed)")
                    self.transcription_queue.put(file_path)
                    self.vad_queue.task_done()
                    continue
                
                # Load previous stage result
                extract_state = self.load_state(file_path, ProcessingStage.EXTRACT_AUDIO)
                if not extract_state or extract_state.status != "completed":
                    logger.error(f"Missing or incomplete extraction for {file_path}")
                    self.vad_queue.task_done()
                    continue
                    
                audio_path = extract_state.result
                
                # Update state to running
                state = ProcessingState(
                    file_path=file_path,
                    stage=ProcessingStage.VAD_SEGMENTATION,
                    status="running",
                    progress=0.0,
                    timestamp=time.time()
                )
                self.save_state(state)
                if self.progress_callback:
                    self.progress_callback(state)
                
                # Perform VAD segmentation
                segments = self.vad.segment_audio(
                    audio_path,
                    str(self.segments_dir),
                    threshold=0.5,
                    min_speech_duration=0.5,
                    min_silence_duration=0.5,
                    margin=0.2
                )
                
                if segments is not None:
                    # Update state to completed
                    state.status = "completed"
                    state.progress = 1.0
                    state.result = segments
                    state.timestamp = time.time()
                    self.save_state(state)
                    if self.progress_callback:
                        self.progress_callback(state)
                    
                    # Add to next stage
                    self.transcription_queue.put(file_path)
                else:
                    # Update state to failed
                    state.status = "failed"
                    state.error = "VAD segmentation failed"
                    state.timestamp = time.time()
                    self.save_state(state)
                    if self.progress_callback:
                        self.progress_callback(state)
                
                self.vad_queue.task_done()
                
            except Exception as e:
                logger.error(f"Error in VAD worker: {e}")
                # Continue processing other items
    
    def _transcription_worker(self):
        """Worker for transcription stage."""
        # Get next available GPU device
        device = self.gpu_devices[0]  # Simplified for now
        
        # Initialize transcriber for this worker
        transcriber = FasterWhisperTranscriber(
            model_size=self.settings.get("model_size", "large-v3"),
            device=device,
            compute_type=self.settings.get("compute_type", "float16") if "cuda" in device else "float32"
        )
        
        while True:
            try:
                file_path = self.transcription_queue.get(timeout=1)
                if file_path is None:  # Shutdown signal
                    break
                    
                logger.info(f"Transcribing {file_path} on {device}")
                
                # Check if we already have a completed state
                state = self.load_state(file_path, ProcessingStage.TRANSCRIPTION)
                if state and state.status == "completed":
                    logger.info(f"Skipping transcription for {file_path} (already completed)")
                    self.alignment_queue.put(file_path)
                    self.transcription_queue.task_done()
                    continue
                
                # Load previous stage result
                vad_state = self.load_state(file_path, ProcessingStage.VAD_SEGMENTATION)
                if not vad_state or vad_state.status != "completed":
                    logger.error(f"Missing or incomplete VAD for {file_path}")
                    self.transcription_queue.task_done()
                    continue
                    
                segment_paths = vad_state.result
                
                # Update state to running
                state = ProcessingState(
                    file_path=file_path,
                    stage=ProcessingStage.TRANSCRIPTION,
                    status="running",
                    progress=0.0,
                    timestamp=time.time()
                )
                self.save_state(state)
                if self.progress_callback:
                    self.progress_callback(state)
                
                # Transcribe each segment
                transcriptions = []
                total_segments = len(segment_paths)
                
                for i, segment_path in enumerate(segment_paths):
                    # Update progress
                    progress = i / total_segments
                    state.progress = progress
                    self.save_state(state)
                    if self.progress_callback:
                        self.progress_callback(state)
                    
                    # Transcribe segment
                    result = transcriber.transcribe(
                        segment_path,
                        language=self.settings.get("language") or None,  # Auto-detect if None
                        task="transcribe",
                        beam_size=5,
                        temperature=0.0
                    )
                    
                    if result:
                        transcriptions.append({
                            "segment_path": segment_path,
                            "result": result
                        })
                
                # Update state to completed
                state.status = "completed"
                state.progress = 1.0
                state.result = transcriptions
                state.timestamp = time.time()
                self.save_state(state)
                if self.progress_callback:
                    self.progress_callback(state)
                
                # Add to next stage
                self.alignment_queue.put(file_path)
                self.transcription_queue.task_done()
                
            except Exception as e:
                logger.error(f"Error in transcription worker: {e}")
                # Continue processing other items

    def _alignment_worker(self):
        """Worker for word alignment stage."""
        aligner = WhisperXAligner(device=self.gpu_devices[0])

        while True:
            try:
                file_path = self.alignment_queue.get(timeout=1)
                if file_path is None:  # Shutdown signal
                    break

                logger.info(f"Aligning words for {file_path}")

                # Check for completed state
                state = self.load_state(file_path, ProcessingStage.ALIGNMENT)
                if state and state.status == "completed":
                    logger.info(f"Skipping alignment for {file_path} (already completed)")
                    self.diarization_queue.put(file_path)
                    self.alignment_queue.task_done()
                    continue

                # Load results from previous stages
                transcription_state = self.load_state(file_path, ProcessingStage.TRANSCRIPTION)
                audio_state = self.load_state(file_path, ProcessingStage.EXTRACT_AUDIO)

                if not all([transcription_state, audio_state]) or transcription_state.status != "completed":
                    logger.error(f"Missing or incomplete transcription for {file_path}")
                    self.alignment_queue.task_done()
                    continue

                # Update state to running
                state = ProcessingState(
                    file_path=file_path,
                    stage=ProcessingStage.ALIGNMENT,
                    status="running",
                    progress=0.0,
                    timestamp=time.time()
                )
                self.save_state(state)
                if self.progress_callback:
                    self.progress_callback(state)

                # Prepare data for alignment
                # The result from transcription is a list of dicts, each with a TranscriptionResult
                all_segments = []
                language = None
                for item in transcription_state.result:
                    transcription_result = item['result']
                    if not language:
                        language = transcription_result['language']
                    # We need to convert the TranscriptionSegment objects back to dicts for whisperx
                    for seg in transcription_result['segments']:
                        all_segments.append({
                            'text': seg['text'],
                            'start': seg['start'],
                            'end': seg['end']
                        })

                # Perform alignment
                aligned_result = aligner.align_words(
                    segments=all_segments,
                    audio_path=audio_state.result,
                    language=language
                )

                if aligned_result:
                    state.status = "completed"
                    state.progress = 1.0
                    state.result = aligned_result
                    state.timestamp = time.time()
                    self.save_state(state)
                    if self.progress_callback:
                        self.progress_callback(state)
                    self.diarization_queue.put(file_path)
                else:
                    state.status = "failed"
                    state.error = "Word alignment failed"
                    state.timestamp = time.time()
                    self.save_state(state)
                    if self.progress_callback:
                        self.progress_callback(state)

                self.alignment_queue.task_done()

            except Exception as e:
                logger.error(f"Error in alignment worker: {e}")

    def _diarization_worker(self):
        """Worker for speaker diarization stage."""
        diarization_enabled = self.settings.get("diarization", True)
        hf_token = self.settings.get("hf_token", None)
        diarizer = PyannoteDiarizer(device=self.gpu_devices[0], hf_token=hf_token) if diarization_enabled else None

        while True:
            try:
                file_path = self.diarization_queue.get(timeout=1)
                if file_path is None:  # Shutdown signal
                    break

                if not diarization_enabled:
                    logger.info(f"Skipping diarization for {file_path} (disabled)")
                    self.merge_queue.put(file_path)
                    self.diarization_queue.task_done()
                    continue

                logger.info(f"Diarizing speakers for {file_path}")

                # Check for completed state
                state = self.load_state(file_path, ProcessingStage.DIARIZATION)
                if state and state.status == "completed":
                    logger.info(f"Skipping diarization for {file_path} (already completed)")
                    self.merge_queue.put(file_path)
                    self.diarization_queue.task_done()
                    continue

                # Load audio path from extraction stage
                audio_state = self.load_state(file_path, ProcessingStage.EXTRACT_AUDIO)
                if not audio_state or audio_state.status != "completed":
                    logger.error(f"Missing or incomplete audio extraction for {file_path}")
                    self.diarization_queue.task_done()
                    continue

                # Update state to running
                state = ProcessingState(
                    file_path=file_path,
                    stage=ProcessingStage.DIARIZATION,
                    status="running",
                    progress=0.0,
                    timestamp=time.time()
                )
                self.save_state(state)
                if self.progress_callback:
                    self.progress_callback(state)

                # Perform diarization
                diarization_result = diarizer.diarize(audio_state.result)

                if diarization_result:
                    state.status = "completed"
                    state.progress = 1.0
                    # Convert result to dict for JSON serialization
                    state.result = [asdict(seg) for seg in diarization_result]
                    state.timestamp = time.time()
                    self.save_state(state)
                    if self.progress_callback:
                        self.progress_callback(state)
                    self.merge_queue.put(file_path)
                else:
                    state.status = "failed"
                    state.error = "Speaker diarization failed"
                    state.timestamp = time.time()
                    self.save_state(state)
                    if self.progress_callback:
                        self.progress_callback(state)

                self.diarization_queue.task_done()

            except Exception as e:
                logger.error(f"Error in diarization worker: {e}")

    def _merge_worker(self):
        """Worker for merging alignment and diarization results."""
        while True:
            try:
                file_path = self.merge_queue.get(timeout=1)
                if file_path is None:  # Shutdown signal
                    break

                logger.info(f"Merging results for {file_path}")

                # Check for completed state
                state = self.load_state(file_path, ProcessingStage.MERGE_SEGMENTS)
                if state and state.status == "completed":
                    logger.info(f"Skipping merge for {file_path} (already completed)")
                    self.export_queue.put(file_path)
                    self.merge_queue.task_done()
                    continue

                # Load results from previous stages
                alignment_state = self.load_state(file_path, ProcessingStage.ALIGNMENT)
                diarization_state = self.load_state(file_path, ProcessingStage.DIARIZATION)

                if not alignment_state or alignment_state.status != "completed":
                    logger.error(f"Missing or incomplete alignment for {file_path}")
                    self.merge_queue.task_done()
                    continue

                # Update state to running
                state = ProcessingState(
                    file_path=file_path,
                    stage=ProcessingStage.MERGE_SEGMENTS,
                    status="running",
                    progress=0.0,
                    timestamp=time.time()
                )
                self.save_state(state)
                if self.progress_callback:
                    self.progress_callback(state)

                # Perform the merge
                aligned_segments = alignment_state.result
                diarization_segments = diarization_state.result if diarization_state else []

                # Create a timeline of speakers from diarization
                speaker_timeline = { (seg['start'], seg['end']): seg['speaker'] for seg in diarization_segments }

                # Assign speaker to each word
                final_segments = []
                for segment in aligned_segments:
                    if 'words' in segment:
                        for word in segment['words']:
                            word_mid_point = word['start'] + (word['end'] - word['start']) / 2
                            assigned_speaker = "UNKNOWN"
                            for (start, end), speaker in speaker_timeline.items():
                                if start <= word_mid_point <= end:
                                    assigned_speaker = speaker
                                    break
                            word['speaker'] = assigned_speaker
                    final_segments.append(segment)

                state.status = "completed"
                state.progress = 1.0
                state.result = final_segments
                state.timestamp = time.time()
                self.save_state(state)
                if self.progress_callback:
                    self.progress_callback(state)
                
                self.export_queue.put(file_path)
                self.merge_queue.task_done()

            except Exception as e:
                logger.error(f"Error in merge worker: {e}")

    def _export_worker(self):
        """Worker for exporting results stage."""
        while True:
            try:
                file_path = self.export_queue.get(timeout=1)
                if file_path is None:  # Shutdown signal
                    break

                logger.info(f"Exporting results for {file_path}")

                # Load final merged data
                merged_state = self.load_state(file_path, ProcessingStage.MERGE_SEGMENTS)
                if not merged_state or merged_state.status != "completed":
                    logger.error(f"Missing or incomplete merge for {file_path}")
                    self.export_queue.task_done()
                    continue

                # Final state update
                state = ProcessingState(
                    file_path=file_path,
                    stage=ProcessingStage.EXPORT,
                    status="completed",
                    progress=1.0,
                    result=merged_state.result, # Pass final result
                    timestamp=time.time()
                )
                self.save_state(state)
                if self.progress_callback:
                    self.progress_callback(state)

                # Notify completion callback with the final result
                if self.completion_callback:
                    self.completion_callback(file_path, state.result)
                
                self.export_queue.task_done()

            except Exception as e:
                logger.error(f"Error in export worker: {e}")

    def start_workers(self):
        """Start all pipeline workers."""
        logger.info("Starting pipeline workers")
        
        worker_map = {
            self._extraction_worker: min(2, self.max_workers),
            self._vad_worker: min(2, self.max_workers),
            self._alignment_worker: 1, # Typically CPU-bound
            self._diarization_worker: 1,
            self._merge_worker: 1,
            self._export_worker: 1,
        }

        # Start CPU-bound workers
        for worker_func, count in worker_map.items():
            for _ in range(count):
                worker = threading.Thread(target=worker_func, daemon=True)
                worker.start()
                self.workers.append(worker)

        # Start GPU-bound workers (transcription)
        for _ in self.gpu_devices:
            worker = threading.Thread(target=self._transcription_worker, daemon=True)
            worker.start()
            self.workers.append(worker)
        
        logger.info(f"Started {len(self.workers)} workers")
    
    def stop_workers(self):
        """Stop all pipeline workers."""
        logger.info("Stopping pipeline workers")
        
        # Send shutdown signals to all queues
        queues = [
            self.extraction_queue, self.vad_queue, self.transcription_queue,
            self.alignment_queue, self.diarization_queue, self.merge_queue,
            self.export_queue
        ]
        for q in queues:
            for _ in range(self.max_workers * 2): # Ensure all workers get signal
                q.put(None)
        
        # Wait for workers to finish
        for worker in self.workers:
            worker.join(timeout=5)
            
        # Shutdown thread pools
        self.cpu_executor.shutdown(wait=True)
        for executor in self.gpu_executors.values():
            executor.shutdown(wait=True)
            
        logger.info("All workers stopped")
    
    def process_file(self, file_path: str) -> Optional[Any]:
        """
        Process a file synchronously.
        
        Args:
            file_path: Path to the input file
            
        Returns:
            Processing result or None if failed
        """
        # Start processing
        self.start_processing(file_path)
        
        # Wait for completion (simplified - in reality, you'd have a more sophisticated mechanism)
        max_wait_time = 300  # 5 minutes
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            # Check if processing is complete
            state = self.load_state(file_path, ProcessingStage.EXPORT)
            if state and state.status == "completed":
                return state.result
                
            time.sleep(1)
        
        logger.warning(f"Processing timeout for {file_path}")
        return None