"""
Performance monitoring and benchmarking with JiWER.
"""
import logging
from typing import List, Dict, Any, Optional
import time
import json
from pathlib import Path

try:
    import jiwer
    JIWER_AVAILABLE = True
except ImportError:
    JIWER_AVAILABLE = False
    jiwer = None

logger = logging.getLogger(__name__)

class PerformanceMonitor:
    """
    Performance monitoring and benchmarking for the transcription pipeline.
    
    Uses JiWER (Jaccard Index Weighted Error Rate) to measure transcription accuracy
    against reference transcriptions, providing WER, MER, and WIL metrics.
    """
    
    def __init__(self, benchmarks_dir: str = "benchmarks"):
        """
        Initialize the performance monitor.
        
        Args:
            benchmarks_dir: Directory to store benchmark results
        """
        if not JIWER_AVAILABLE:
            raise ImportError(
                "jiwer is not installed. "
                "Install it with: pip install jiwer"
            )
            
        self.benchmarks_dir = Path(benchmarks_dir)
        self.benchmarks_dir.mkdir(exist_ok=True)
    
    def calculate_wer(self, 
                     reference: str, 
                     hypothesis: str) -> Dict[str, float]:
        """
        Calculate Word Error Rate (WER) and related metrics.
        
        Args:
            reference: Reference (ground truth) transcription
            hypothesis: Hypothesis (generated) transcription
            
        Returns:
            Dictionary with WER, MER, WIL, and detailed metrics
        """
        try:
            # Calculate metrics using JiWER
            result = jiwer.process_words(reference, hypothesis)
            
            return {
                "wer": result.wer,           # Word Error Rate
                "mer": result.mer,           # Match Error Rate
                "wil": result.wil,           # Word Information Lost
                "wip": result.wip,           # Word Information Preserved
                "hits": result.hits,         # Correct words
                "substitutions": result.substitutions,  # Substituted words
                "deletions": result.deletions,          # Deleted words
                "insertions": result.insertions,        # Inserted words
                "reference_length": len(result.references), # Reference length
                "hypothesis_length": len(result.hypotheses)  # Hypothesis length
            }
        except Exception as e:
            logger.error(f"Error calculating WER: {e}")
            return {
                "wer": -1.0,
                "mer": -1.0,
                "wil": -1.0,
                "wip": -1.0,
                "error": str(e)
            }
    
    def benchmark_transcription(self,
                              audio_file: str,
                              reference_text: str,
                              transcription_result: str,
                              language: str = "en") -> Dict[str, Any]:
        """
        Benchmark a transcription result against reference text.
        
        Args:
            audio_file: Path to the audio file
            reference_text: Reference transcription
            transcription_result: Generated transcription
            language: Language code
            
        Returns:
            Benchmark results dictionary
        """
        # Calculate accuracy metrics
        metrics = self.calculate_wer(reference_text, transcription_result)
        
        # Create benchmark result
        benchmark_result = {
            "audio_file": audio_file,
            "language": language,
            "reference_length": len(reference_text.split()),
            "hypothesis_length": len(transcription_result.split()),
            "metrics": metrics,
            "timestamp": time.time()
        }
        
        return benchmark_result
    
    def save_benchmark_result(self, 
                            benchmark_result: Dict[str, Any],
                            benchmark_name: str = None) -> str:
        """
        Save benchmark result to file.
        
        Args:
            benchmark_result: Benchmark result dictionary
            benchmark_name: Optional name for the benchmark
            
        Returns:
            Path to the saved benchmark file
        """
        if not benchmark_name:
            benchmark_name = f"benchmark_{int(time.time())}"
            
        benchmark_file = self.benchmarks_dir / f"{benchmark_name}.json"
        
        try:
            with open(benchmark_file, 'w') as f:
                json.dump(benchmark_result, f, indent=2)
            logger.info(f"Benchmark result saved to {benchmark_file}")
            return str(benchmark_file)
        except Exception as e:
            logger.error(f"Failed to save benchmark result: {e}")
            return ""
    
    def compare_benchmarks(self, 
                          benchmark_files: List[str]) -> Dict[str, Any]:
        """
        Compare multiple benchmark results.
        
        Args:
            benchmark_files: List of paths to benchmark result files
            
        Returns:
            Comparison results dictionary
        """
        results = []
        
        # Load benchmark results
        for file_path in benchmark_files:
            try:
                with open(file_path, 'r') as f:
                    result = json.load(f)
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to load benchmark {file_path}: {e}")
                continue
        
        if not results:
            return {}
        
        # Calculate statistics
        total_wer = sum(r["metrics"]["wer"] for r in results if r["metrics"]["wer"] >= 0)
        valid_results = len([r for r in results if r["metrics"]["wer"] >= 0])
        
        comparison = {
            "total_benchmarks": len(results),
            "valid_benchmarks": valid_results,
            "average_wer": total_wer / valid_results if valid_results > 0 else -1,
            "min_wer": min([r["metrics"]["wer"] for r in results if r["metrics"]["wer"] >= 0], default=-1),
            "max_wer": max([r["metrics"]["wer"] for r in results if r["metrics"]["wer"] >= 0], default=-1),
            "results": results
        }
        
        return comparison
    
    def create_benchmark_report(self, 
                              comparison: Dict[str, Any],
                              report_file: str = None) -> str:
        """
        Create a benchmark report in a readable format.
        
        Args:
            comparison: Comparison results from compare_benchmarks
            report_file: Optional path to save the report
            
        Returns:
            Report content as string
        """
        if not comparison:
            report = "No benchmark data available."
            if report_file:
                with open(report_file, 'w') as f:
                    f.write(report)
            return report
        
        report = f"""
Transcription Benchmark Report
==============================

Total Benchmarks: {comparison['total_benchmarks']}
Valid Benchmarks: {comparison['valid_benchmarks']}

Accuracy Metrics:
-----------------
Average WER: {comparison['average_wer']:.2%}
Min WER: {comparison['min_wer']:.2%}
Max WER: {comparison['max_wer']:.2%}

Detailed Results:
-----------------
"""
        
        for i, result in enumerate(comparison['results'], 1):
        
            wer = result['metrics']['wer']
            wer_display = f"{wer:.2%}" if wer >= 0 else "N/A"
            report += f"{i}. {result['audio_file']} (WER: {wer_display})\n"
        if report_file:
            with open(report_file, 'w') as f:
                f.write(report)
                
        return report

class PerformanceTimer:
    """
    Simple performance timer for measuring execution times.
    """
    
    def __init__(self):
        self.start_time = None
        self.end_time = None
    
    def start(self):
        """Start the timer."""
        self.start_time = time.perf_counter()
    
    def stop(self) -> float:
        """
        Stop the timer and return elapsed time in seconds.
        
        Returns:
            Elapsed time in seconds
        """
        self.end_time = time.perf_counter()
        return self.elapsed_time()
    
    def elapsed_time(self) -> float:
        """
        Get elapsed time without stopping the timer.
        
        Returns:
            Elapsed time in seconds
        """
        if self.start_time is None:
            return 0.0
        end_time = self.end_time or time.perf_counter()
        return end_time - self.start_time
    
    def format_time(self, seconds: float) -> str:
        """
        Format time in a human-readable way.
        
        Args:
            seconds: Time in seconds
            
        Returns:
            Formatted time string
        """
        if seconds < 1:
            return f"{seconds*1000:.2f}ms"
        elif seconds < 60:
            return f"{seconds:.2f}s"
        else:
            minutes = int(seconds // 60)
            secs = seconds % 60
            return f"{minutes}m {secs:.2f}s"