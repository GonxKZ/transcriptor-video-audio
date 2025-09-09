"""
Basic tests for the Transcriptor application.
"""
import sys
import os
import pytest
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtTest import QTest

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from transcriptor.ui.main_window import MainWindow
from transcriptor.audio.preprocessor import AudioPreprocessor
from transcriptor.utils.config import ConfigManager

class TestConfigManager:
    """Test the configuration manager."""
    
    def test_config_creation(self):
        """Test creating a configuration manager."""
        config = ConfigManager()
        assert config is not None
        assert config.settings is not None
    
    def test_config_save_load(self):
        """Test saving and loading configuration."""
        config = ConfigManager()
        original_model = config.settings.model_size
        config.settings.model_size = "test_model"
        assert config.save_settings() == True
        config.settings.model_size = "other_model"
        assert config.load_settings() == True
        assert config.settings.model_size == "test_model"
        # Restore original value
        config.settings.model_size = original_model
        config.save_settings()

class TestAudioPreprocessor:
    """Test the audio preprocessor."""
    
    def test_preprocessor_creation(self):
        """Test creating an audio preprocessor."""
        preprocessor = AudioPreprocessor("/tmp/test_workspace")
        assert preprocessor is not None
        assert preprocessor.workspace_dir == "/tmp/test_workspace"

class TestMainWindow:
    """Test the main window."""
    
    @pytest.fixture
    def app(self):
        """Create a QApplication instance."""
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        return app
    
    @pytest.fixture
    def window(self, app):
        """Create a main window instance."""
        return MainWindow()
    
    def test_window_creation(self, window):
        """Test creating the main window."""
        assert window is not None
        assert window.windowTitle() == "Transcriptor de Video/Audio"
    
    def test_window_size(self, window):
        """Test the initial window size."""
        assert window.width() == 1200
        assert window.height() == 800
    
    def test_project_area_exists(self, window):
        """Test that the project area exists."""
        assert hasattr(window, 'project_area')
        assert window.project_area is not None
    
    def test_process_panel_exists(self, window):
        """Test that the process panel exists."""
        assert hasattr(window, 'process_panel')
        assert window.process_panel is not None
    
    def test_transcription_editor_exists(self, window):
        """Test that the transcription editor exists."""
        assert hasattr(window, 'transcription_editor')
        assert window.transcription_editor is not None

if __name__ == "__main__":
    pytest.main([__file__])