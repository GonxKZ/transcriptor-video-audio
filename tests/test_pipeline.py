"""
Tests for the streaming pipeline.
"""
import sys
import os
import pytest
import tempfile
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from transcriptor.pipeline.streaming import StreamingPipeline, ProcessingStage, ProcessingState

class TestStreamingPipeline:
    """Test the streaming pipeline."""
    
    @pytest.fixture
    def workspace_dir(self):
        """Create a temporary workspace directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir
    
    @pytest.fixture
    def pipeline(self, workspace_dir):
        """Create a streaming pipeline instance."""
        return StreamingPipeline(workspace_dir, max_workers=2)
    
    def test_pipeline_creation(self, pipeline):
        """Test creating the streaming pipeline."""
        assert pipeline is not None
        assert hasattr(pipeline, 'workspace_dir')
        assert hasattr(pipeline, 'temp_dir')
        assert hasattr(pipeline, 'states_dir')
        assert hasattr(pipeline, 'segments_dir')
    
    def test_state_file_path(self, pipeline):
        """Test getting state file path."""
        file_path = "/test/audio.mp3"
        stage = ProcessingStage.EXTRACT_AUDIO
        state_file = pipeline.get_state_file_path(file_path, stage)
        assert state_file is not None
        assert state_file.suffix == ".json"
    
    def test_save_load_state(self, pipeline):
        """Test saving and loading state."""
        state = ProcessingState(
            file_path="/test/audio.mp3",
            stage=ProcessingStage.EXTRACT_AUDIO,
            status="completed",
            progress=1.0,
            result="/test/processed.wav"
        )
        
        # Save state
        pipeline.save_state(state)
        
        # Load state
        loaded_state = pipeline.load_state("/test/audio.mp3", ProcessingStage.EXTRACT_AUDIO)
        assert loaded_state is not None
        assert loaded_state.file_path == state.file_path
        assert loaded_state.stage == state.stage
        assert loaded_state.status == state.status
        assert loaded_state.progress == state.progress
        assert loaded_state.result == state.result
    
    def test_processing_state_serialization(self):
        """Test ProcessingState serialization."""
        state = ProcessingState(
            file_path="/test/audio.mp3",
            stage=ProcessingStage.EXTRACT_AUDIO,
            status="running",
            progress=0.5,
            result=None,
            error=None
        )
        
        # Convert to dict
        state_dict = state.to_dict()
        assert isinstance(state_dict, dict)
        assert state_dict["file_path"] == state.file_path
        assert state_dict["stage"] == state.stage.value
        assert state_dict["status"] == state.status
        assert state_dict["progress"] == state.progress
        
        # Create from dict
        restored_state = ProcessingState.from_dict(state_dict)
        assert restored_state.file_path == state.file_path
        assert restored_state.stage == state.stage
        assert restored_state.status == state.status
        assert restored_state.progress == state.progress

if __name__ == "__main__":
    pytest.main([__file__])