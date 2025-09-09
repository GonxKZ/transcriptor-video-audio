"""
ONNX Runtime with DirectML backend for Windows compatibility.
"""
import os
import logging
from typing import Optional, List, Dict, Any
from pathlib import Path

try:
    import onnxruntime as ort
    ONNXRUNTIME_AVAILABLE = True
except ImportError:
    ONNXRUNTIME_AVAILABLE = False
    ort = None

logger = logging.getLogger(__name__)

class ONNXTranscriber:
    """
    Transcription using ONNX Runtime with DirectML backend for Windows.
    
    This provides an alternative to PyTorch/CUDA for systems without NVIDIA GPUs,
    using ONNX models that can run on DirectX 12 compatible hardware via DirectML.
    """
    
    def __init__(self, 
                 model_path: str,
                 device: str = "dml",  # dml for DirectML, cpu for CPU
                 inter_op_num_threads: int = 1,
                 intra_op_num_threads: int = 4):
        """
        Initialize the ONNX transcriber.
        
        Args:
            model_path: Path to the ONNX model file
            device: Device to use ("dml" for DirectML, "cpu" for CPU)
            inter_op_num_threads: Number of threads for parallel execution
            intra_op_num_threads: Number of threads for intra-operator parallelism
        """
        if not ONNXRUNTIME_AVAILABLE:
            raise ImportError(
                "onnxruntime is not installed. "
                "Install it with: pip install onnxruntime-directml"
            )
            
        self.model_path = Path(model_path)
        if not self.model_path.exists():
            raise FileNotFoundError(f"Model file not found: {model_path}")
            
        self.device = device
        self.inter_op_num_threads = inter_op_num_threads
        self.intra_op_num_threads = intra_op_num_threads
        self.session = None
        
        # Check if DirectML is available
        self.dml_available = "DmlExecutionProvider" in ort.get_available_providers()
        
        self._load_model()
    
    def _load_model(self):
        """Load the ONNX model."""
        try:
            logger.info(f"Loading ONNX model from {self.model_path}")
            
            # Configure execution providers
            providers = []
            if self.device == "dml" and self.dml_available:
                providers.append("DmlExecutionProvider")
                logger.info("Using DirectML execution provider")
            else:
                providers.append("CPUExecutionProvider")
                logger.info("Using CPU execution provider")
            
            # Configure session options
            sess_options = ort.SessionOptions()
            sess_options.inter_op_num_threads = self.inter_op_num_threads
            sess_options.intra_op_num_threads = self.intra_op_num_threads
            sess_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
            
            # Create session
            self.session = ort.InferenceSession(
                str(self.model_path),
                sess_options=sess_options,
                providers=providers
            )
            
            logger.info("ONNX model loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load ONNX model: {e}")
            raise
    
    def transcribe(self, 
                   audio_data: Any,
                   language: Optional[str] = None,
                   task: str = "transcribe",
                   **kwargs) -> Optional[Dict[str, Any]]:
        """
        Transcribe audio using the ONNX model.
        
        Args:
            audio_data: Audio data to transcribe (format depends on model)
            language: Language code (None for auto-detection)
            task: Task type ("transcribe" or "translate")
            **kwargs: Additional arguments
            
        Returns:
            Transcription result or None if failed
        """
        try:
            logger.info("Starting ONNX transcription")
            
            # Prepare inputs
            # Note: The exact input format depends on the specific ONNX model
            # This is a simplified example - a real implementation would need
            # to match the model's expected input format
            inputs = {
                "audio": audio_data,  # This would need to be properly formatted
            }
            
            if language:
                inputs["language"] = language
            if task:
                inputs["task"] = task
                
            # Run inference
            outputs = self.session.run(None, inputs)
            
            # Process outputs
            # Note: The exact output format depends on the specific ONNX model
            # This is a simplified example
            result = {
                "segments": [],  # Would be populated with transcription segments
                "language": language or "en",  # Would be detected by model
            }
            
            logger.info("ONNX transcription completed successfully")
            return result
            
        except Exception as e:
            logger.error(f"Error during ONNX transcription: {e}")
            return None
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the loaded model.
        
        Returns:
            Dictionary with model information
        """
        if not self.session:
            return {}
            
        return {
            "model_path": str(self.model_path),
            "device": self.device,
            "providers": self.session.get_providers(),
            "input_names": [input.name for input in self.session.get_inputs()],
            "output_names": [output.name for output in self.session.get_outputs()],
            "dml_available": self.dml_available
        }

class ONNXModelConverter:
    """
    Utility class for converting PyTorch models to ONNX format.
    
    This can be used to create ONNX versions of Whisper models for use
    with the ONNXTranscriber.
    """
    
    @staticmethod
    def convert_whisper_model(pytorch_model_path: str, 
                            onnx_model_path: str,
                            opset_version: int = 13) -> bool:
        """
        Convert a PyTorch Whisper model to ONNX format.
        
        Args:
            pytorch_model_path: Path to the PyTorch model
            onnx_model_path: Path to save the ONNX model
            opset_version: ONNX opset version to use
            
        Returns:
            True if conversion successful, False otherwise
        """
        try:
            logger.info(f"Converting PyTorch model {pytorch_model_path} to ONNX")
            
            # This is a simplified example - a real implementation would need
            # to properly load the PyTorch model and trace/export it to ONNX
            
            # Import required modules
            import torch
            
            # Load PyTorch model
            model = torch.load(pytorch_model_path)
            
            # Create dummy input (this would need to match the model's expected input)
            dummy_input = torch.randn(1, 80, 3000)  # Example shape
            
            # Export to ONNX
            torch.onnx.export(
                model,
                dummy_input,
                onnx_model_path,
                opset_version=opset_version,
                export_params=True,
                do_constant_folding=True,
                input_names=["audio"],
                output_names=["output"],
                dynamic_axes={
                    "audio": {0: "batch_size", 1: "n_mels", 2: "time"},
                    "output": {0: "batch_size", 1: "sequence"}
                }
            )
            
            logger.info(f"Model converted successfully to {onnx_model_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to convert model to ONNX: {e}")
            return False

def check_directml_availability() -> bool:
    """
    Check if DirectML is available on this system.
    
    Returns:
        True if DirectML is available, False otherwise
    """
    if not ONNXRUNTIME_AVAILABLE:
        return False
        
    return "DmlExecutionProvider" in ort.get_available_providers()

def get_available_providers() -> List[str]:
    """
    Get list of available ONNX Runtime execution providers.
    
    Returns:
        List of available providers
    """
    if not ONNXRUNTIME_AVAILABLE:
        return []
        
    return ort.get_available_providers()