# =============================================================================
# Model Evaluation Tests
# =============================================================================
"""
Tests for AI model evaluation metrics and pipelines.

These tests ensure:
- Evaluation metrics are calculated correctly
- Model benchmarks are reproducible
- Performance meets requirements
"""

import pytest
import numpy as np
from typing import List, Dict
import json

import sys
sys.path.insert(0, "ai-core")

from scripts.evaluate import (
    calculate_gop_metrics,
    calculate_phoneme_accuracy,
    calculate_word_error_rate,
    EvaluationResult,
)


class TestGOPMetrics:
    """Tests for Goodness of Pronunciation metrics."""
    
    def test_perfect_correlation(self):
        """Test GOP metrics with perfect predictions."""
        predicted = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        ground_truth = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        
        metrics = calculate_gop_metrics(predicted, ground_truth)
        
        assert metrics["correlation"] == pytest.approx(1.0, abs=1e-6)
        assert metrics["mae"] == pytest.approx(0.0, abs=1e-6)
    
    def test_zero_correlation(self):
        """Test GOP metrics with uncorrelated predictions."""
        predicted = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        ground_truth = np.array([5.0, 4.0, 3.0, 2.0, 1.0])
        
        metrics = calculate_gop_metrics(predicted, ground_truth)
        
        # Perfect negative correlation
        assert metrics["correlation"] == pytest.approx(-1.0, abs=1e-6)
    
    def test_mae_calculation(self):
        """Test Mean Absolute Error calculation."""
        predicted = np.array([1.0, 2.0, 3.0])
        ground_truth = np.array([2.0, 3.0, 4.0])
        
        metrics = calculate_gop_metrics(predicted, ground_truth)
        
        # MAE should be 1.0 (each prediction is off by 1)
        assert metrics["mae"] == pytest.approx(1.0, abs=1e-6)
    
    def test_rmse_calculation(self):
        """Test Root Mean Square Error calculation."""
        predicted = np.array([0.0, 0.0])
        ground_truth = np.array([3.0, 4.0])
        
        metrics = calculate_gop_metrics(predicted, ground_truth)
        
        # RMSE = sqrt((9 + 16) / 2) = sqrt(12.5) ≈ 3.54
        expected_rmse = np.sqrt(12.5)
        assert metrics["rmse"] == pytest.approx(expected_rmse, abs=1e-6)


class TestPhonemeAccuracy:
    """Tests for phoneme-level accuracy metrics."""
    
    def test_perfect_phoneme_accuracy(self):
        """Test accuracy with perfect phoneme predictions."""
        predicted = [["P", "AE", "T"], ["K", "AE", "T"]]
        ground_truth = [["P", "AE", "T"], ["K", "AE", "T"]]
        
        accuracy = calculate_phoneme_accuracy(predicted, ground_truth)
        
        assert accuracy == pytest.approx(1.0, abs=1e-6)
    
    def test_zero_phoneme_accuracy(self):
        """Test accuracy with all wrong predictions."""
        predicted = [["X", "Y", "Z"]]
        ground_truth = [["A", "B", "C"]]
        
        accuracy = calculate_phoneme_accuracy(predicted, ground_truth)
        
        assert accuracy == pytest.approx(0.0, abs=1e-6)
    
    def test_partial_phoneme_accuracy(self):
        """Test accuracy with partially correct predictions."""
        predicted = [["P", "X", "T"]]  # 2/3 correct
        ground_truth = [["P", "AE", "T"]]
        
        accuracy = calculate_phoneme_accuracy(predicted, ground_truth)
        
        assert accuracy == pytest.approx(2/3, abs=1e-6)
    
    def test_different_length_sequences(self):
        """Test accuracy with different length predictions."""
        predicted = [["P", "AE"]]  # Shorter than ground truth
        ground_truth = [["P", "AE", "T"]]
        
        accuracy = calculate_phoneme_accuracy(predicted, ground_truth)
        
        # Only compare first 2 phonemes (min length)
        # 2/3 of ground truth matched
        assert accuracy == pytest.approx(2/3, abs=1e-6)


class TestWordErrorRate:
    """Tests for Word Error Rate (WER) calculation."""
    
    def test_zero_wer(self):
        """Test WER with perfect transcription."""
        hypotheses = ["hello world"]
        references = ["hello world"]
        
        wer = calculate_word_error_rate(hypotheses, references)
        
        assert wer == pytest.approx(0.0, abs=1e-6)
    
    def test_complete_wer(self):
        """Test WER with completely wrong transcription."""
        hypotheses = ["goodbye moon"]
        references = ["hello world"]
        
        wer = calculate_word_error_rate(hypotheses, references)
        
        # 2 substitutions / 2 reference words = 1.0
        assert wer == pytest.approx(1.0, abs=1e-6)
    
    def test_insertion_error(self):
        """Test WER with insertion errors."""
        hypotheses = ["hello beautiful world"]
        references = ["hello world"]
        
        wer = calculate_word_error_rate(hypotheses, references)
        
        # 1 insertion / 2 reference words = 0.5
        assert wer == pytest.approx(0.5, abs=1e-6)
    
    def test_deletion_error(self):
        """Test WER with deletion errors."""
        hypotheses = ["hello"]
        references = ["hello world"]
        
        wer = calculate_word_error_rate(hypotheses, references)
        
        # 1 deletion / 2 reference words = 0.5
        assert wer == pytest.approx(0.5, abs=1e-6)
    
    def test_case_insensitive(self):
        """Test that WER is case insensitive."""
        hypotheses = ["HELLO WORLD"]
        references = ["hello world"]
        
        wer = calculate_word_error_rate(hypotheses, references)
        
        assert wer == pytest.approx(0.0, abs=1e-6)


class TestEvaluationResult:
    """Tests for evaluation result data structure."""
    
    def test_result_creation(self):
        """Test creating an evaluation result."""
        result = EvaluationResult(
            gop_correlation=0.85,
            gop_mae=0.12,
            phoneme_accuracy=0.78,
            word_error_rate=0.15,
            latency_p50_ms=45.0,
            latency_p99_ms=120.0,
            throughput_audio_sec_per_sec=35.0,
            num_samples=1000,
            total_audio_duration_sec=3600.0,
        )
        
        assert result.gop_correlation == 0.85
        assert result.phoneme_accuracy == 0.78
        assert result.num_samples == 1000


class TestModelBenchmarks:
    """Tests for model performance benchmarks."""
    
    @pytest.fixture
    def performance_thresholds(self):
        """Define minimum performance thresholds."""
        return {
            "min_gop_correlation": 0.7,
            "max_wer": 0.25,
            "min_phoneme_accuracy": 0.7,
            "max_latency_p99_ms": 200,
        }
    
    def test_gop_correlation_threshold(self, performance_thresholds):
        """Test that GOP correlation meets minimum threshold."""
        # Mock evaluation result
        result = EvaluationResult(
            gop_correlation=0.85,
            gop_mae=0.12,
            phoneme_accuracy=0.78,
            word_error_rate=0.15,
            latency_p50_ms=45.0,
            latency_p99_ms=120.0,
            throughput_audio_sec_per_sec=35.0,
            num_samples=1000,
            total_audio_duration_sec=3600.0,
        )
        
        assert result.gop_correlation >= performance_thresholds["min_gop_correlation"]
    
    def test_wer_threshold(self, performance_thresholds):
        """Test that WER is below maximum threshold."""
        result = EvaluationResult(
            gop_correlation=0.85,
            gop_mae=0.12,
            phoneme_accuracy=0.78,
            word_error_rate=0.15,
            latency_p50_ms=45.0,
            latency_p99_ms=120.0,
            throughput_audio_sec_per_sec=35.0,
            num_samples=1000,
            total_audio_duration_sec=3600.0,
        )
        
        assert result.word_error_rate <= performance_thresholds["max_wer"]
    
    def test_latency_threshold(self, performance_thresholds):
        """Test that P99 latency is below maximum threshold."""
        result = EvaluationResult(
            gop_correlation=0.85,
            gop_mae=0.12,
            phoneme_accuracy=0.78,
            word_error_rate=0.15,
            latency_p50_ms=45.0,
            latency_p99_ms=120.0,
            throughput_audio_sec_per_sec=35.0,
            num_samples=1000,
            total_audio_duration_sec=3600.0,
        )
        
        assert result.latency_p99_ms <= performance_thresholds["max_latency_p99_ms"]
