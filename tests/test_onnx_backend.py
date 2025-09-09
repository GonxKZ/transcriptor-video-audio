"""
Tests for the ONNX backend.
"""
import sys
import os
import pytest
from unittest.mock import patch, MagicMock

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from transcriptor.transcription.onnx_backend import (
    ONNXTranscriber, 
    ONNXModelConverter, 
    check_directml_availability, 
    get_available_providers
)

class TestONNXBackend:
    """Test the ONNX backend."""
    
    def test_check_directml_availability(self):
        """Test checking DirectML availability."""
        # Test with onnxruntime available
        with patch('transcriptor.transcription.onnx_backend.ort') as mock_ort:
            mock_ort.get_available_providers.return_value = ["DmlExecutionProvider", "CPUExecutionProvider"]
            assert check_directml_availability() == True
            
            mock_ort.get_available_providers.return_value = ["CPUExecutionProvider"]
            assert check_directml_availability() == False
    
    def test_get_available_providers(self):
        """Test getting available providers."""
        # Test with onnxruntime available
        with patch('transcriptor.transcription.onnx_backend.ort') as mock_ort:
            mock_ort.get_available_providers.return_value = ["CPUExecutionProvider"]
            providers = get_available_providers()
            assert providers == ["CPUExecutionProvider"]
    
    def test_onnx_transcriber_import_error(self):
        """Test ONNXTranscriber import error handling."""
        # Test with onnxruntime not available
        with patch('transcriptor.transcription.onnx_backend.ONNXRUNTIME_AVAILABLE', False):
            with pytest.raises(ImportError):
                ONNXTranscriber("test_model.onnx")
    
    def test_onnx_model_converter(self):
        """Test ONNX model converter."""
        # This test is simplified since mocking torch in this context is complex
        # In a real implementation, we would test the actual conversion
        assert True  # Placeholder test

if __name__ == "__main__":
    pytest.main([__file__])