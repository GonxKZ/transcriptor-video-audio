"""
Tests for the advanced transcription editor.
"""
import sys
import os
import pytest
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from transcriptor.ui.editor import TranscriptionEditor, Word, Segment

class TestTranscriptionEditor:
    """Test the advanced transcription editor."""
    
    @pytest.fixture
    def app(self):
        """Create a QApplication instance."""
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        return app
    
    @pytest.fixture
    def editor(self, app):
        """Create a transcription editor instance."""
        return TranscriptionEditor()
    
    def test_editor_creation(self, editor):
        """Test creating the transcription editor."""
        assert editor is not None
        assert hasattr(editor, 'segments_tree')
        assert hasattr(editor, 'text_editor')
    
    def test_load_transcription(self, editor):
        """Test loading transcription segments."""
        # Create sample segments
        segments = [
            Segment(
                id=0,
                start_time=0.0,
                end_time=1.0,
                words=[
                    Word(text="Hello", start_time=0.0, end_time=0.5, confidence=0.95),
                    Word(text="world", start_time=0.5, end_time=1.0, confidence=0.98),
                ],
                text="Hello world"
            )
        ]
        
        # Load segments
        editor.load_transcription(segments)
        
        # Check that segments were loaded
        assert len(editor.segments) == 1
        assert editor.segments[0].id == 0
        assert len(editor.segments[0].words) == 2
    
    def test_get_transcription_text(self, editor):
        """Test getting transcription text."""
        # Create sample segments
        segments = [
            Segment(
                id=0,
                start_time=0.0,
                end_time=1.0,
                words=[
                    Word(text="Hello", start_time=0.0, end_time=0.5, confidence=0.95),
                    Word(text="world", start_time=0.5, end_time=1.0, confidence=0.98),
                ],
                text="Hello world"
            )
        ]
        
        # Load segments
        editor.load_transcription(segments)
        
        # Get text
        text = editor.get_transcription_text()
        assert isinstance(text, str)
    
    def test_format_timestamp(self, editor):
        """Test timestamp formatting."""
        # Test SRT format
        srt_timestamp = editor.format_timestamp(3661.123)  # 1h 1m 1.123s
        assert srt_timestamp == "01:01:01,123"
        
        # Test VTT format
        vtt_timestamp = editor.format_timestamp(3661.123, vtt_format=True)
        assert vtt_timestamp == "01:01:01.123"

if __name__ == "__main__":
    pytest.main([__file__])