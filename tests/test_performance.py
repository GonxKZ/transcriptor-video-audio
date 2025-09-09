"""
Tests for the performance monitoring module.
"""
import sys
import os
import pytest
import tempfile
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from transcriptor.utils.performance import PerformanceMonitor, PerformanceTimer

class TestPerformanceMonitor:
    """Test the performance monitor."""
    
    @pytest.fixture
    def benchmarks_dir(self):
        """Create a temporary benchmarks directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir
    
    @pytest.fixture
    def monitor(self, benchmarks_dir):
        """Create a performance monitor instance."""
        return PerformanceMonitor(benchmarks_dir)
    
    def test_monitor_creation(self, monitor):
        """Test creating the performance monitor."""
        assert monitor is not None
        assert hasattr(monitor, 'benchmarks_dir')
    
    def test_calculate_wer(self, monitor):
        """Test calculating WER."""
        reference = "hello world"
        hypothesis = "hello world"
        
        metrics = monitor.calculate_wer(reference, hypothesis)
        assert metrics["wer"] == 0.0
        assert metrics["mer"] == 0.0
        assert metrics["wil"] == 0.0
        assert metrics["hits"] == 2
        assert metrics["substitutions"] == 0
        assert metrics["deletions"] == 0
        assert metrics["insertions"] == 0
    
    def test_benchmark_transcription(self, monitor):
        """Test benchmarking transcription."""
        result = monitor.benchmark_transcription(
            "test.wav",
            "hello world",
            "hello world",
            "en"
        )
        
        assert result["audio_file"] == "test.wav"
        assert result["language"] == "en"
        assert result["metrics"]["wer"] == 0.0
    
    def test_save_benchmark_result(self, monitor):
        """Test saving benchmark result."""
        benchmark_result = {
            "audio_file": "test.wav",
            "language": "en",
            "metrics": {"wer": 0.0}
        }
        
        file_path = monitor.save_benchmark_result(benchmark_result, "test_benchmark")
        assert file_path != ""
        assert Path(file_path).exists()
    
    def test_compare_benchmarks(self, monitor):
        """Test comparing benchmarks."""
        # Create test benchmark files
        benchmark1 = {
            "audio_file": "test1.wav",
            "language": "en",
            "metrics": {"wer": 0.1}
        }
        
        benchmark2 = {
            "audio_file": "test2.wav",
            "language": "en",
            "metrics": {"wer": 0.2}
        }
        
        file1 = monitor.save_benchmark_result(benchmark1, "benchmark1")
        file2 = monitor.save_benchmark_result(benchmark2, "benchmark2")
        
        comparison = monitor.compare_benchmarks([file1, file2])
        assert comparison["total_benchmarks"] == 2
        assert abs(comparison["average_wer"] - 0.15) < 0.0001

class TestPerformanceTimer:
    """Test the performance timer."""
    
    def test_timer(self):
        """Test the performance timer."""
        timer = PerformanceTimer()
        
        # Test without starting
        assert timer.elapsed_time() == 0.0
        
        # Test with starting and stopping
        timer.start()
        # Simulate some work
        import time
        time.sleep(0.01)  # 10ms
        elapsed = timer.stop()
        
        assert elapsed > 0.0
        assert elapsed < 1.0  # Should be less than 1 second
    
    def test_format_time(self):
        """Test formatting time."""
        timer = PerformanceTimer()
        
        # Test milliseconds
        formatted = timer.format_time(0.005)
        assert "ms" in formatted
        
        # Test seconds
        formatted = timer.format_time(30.5)
        assert "s" in formatted
        
        # Test minutes
        formatted = timer.format_time(125.5)
        assert "m" in formatted

if __name__ == "__main__":
    pytest.main([__file__])