"""
Unit tests for metric calculator utilities
"""
import unittest
from datetime import datetime, timedelta
from src.utils.metric_calculator import MetricCalculator, CostCalculator

class TestMetricCalculator(unittest.TestCase):
    """Test cases for MetricCalculator class"""
    
    def test_calculate_anomaly_threshold(self):
        """Test anomaly threshold calculation"""
        # Test with normal distribution
        values = [10, 12, 11, 13, 9, 14, 10, 12, 11, 13]
        threshold = MetricCalculator.calculate_anomaly_threshold(values, sensitivity=2.0)
        
        # Should be mean + 2*std_dev
        expected_mean = sum(values) / len(values)
        self.assertGreater(threshold, expected_mean)
        
        # Test with empty list
        threshold_empty = MetricCalculator.calculate_anomaly_threshold([])
        self.assertEqual(threshold_empty, 0.0)
        
        # Test with single value
        threshold_single = MetricCalculator.calculate_anomaly_threshold([10])
        self.assertEqual(threshold_single, 0.0)
    
    def test_detect_trend(self):
        """Test trend detection"""
        # Increasing trend
        increasing_values = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 15, 20, 25, 30, 35]
        trend = MetricCalculator.detect_trend(increasing_values, window_size=5)
        self.assertEqual(trend, 'increasing')
        
        # Decreasing trend
        decreasing_values = [35, 30, 25, 20, 15, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1]
        trend = MetricCalculator.detect_trend(decreasing_values, window_size=5)
        self.assertEqual(trend, 'decreasing')
        
        # Stable trend
        stable_values = [10, 11, 9, 10, 12, 9, 11, 10, 12, 9, 10, 11, 9, 10, 12]
        trend = MetricCalculator.detect_trend(stable_values, window_size=5)
        self.assertEqual(trend, 'stable')
        
        # Insufficient data
        short_values = [1, 2, 3]
        trend = MetricCalculator.detect_trend(short_values, window_size=5)
        self.assertEqual(trend, 'stable')
    
    def test_calculate_percentiles(self):
        """Test percentile calculations"""
        values = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        percentiles = MetricCalculator.calculate_percentiles(values)
        
        self.assertIn('p50', percentiles)
        self.assertIn('p90', percentiles)
        self.assertIn('p95', percentiles)
        self.assertIn('p99', percentiles)
        
        # p50 should be median
        self.assertEqual(percentiles['p50'], 5.5)
        
        # p90 should be close to 9
        self.assertAlmostEqual(percentiles['p90'], 9.1, places=1)
        
        # Test with empty list
        empty_percentiles = MetricCalculator.calculate_percentiles([])
        self.assertEqual(empty_percentiles, {})
    
    def test_is_seasonal_pattern(self):
        """Test seasonal pattern detection"""
        # Create mock data with daily pattern
        base_time = datetime(2023, 1, 1, 0, 0, 0)
        timestamps = []
        values = []
        
        # Generate 3 days of hourly data with pattern
        for day in range(3):
            for hour in range(24):
                timestamp = base_time + timedelta(days=day, hours=hour)
                timestamps.append(timestamp)
                
                # Create pattern: higher values during business hours
                if 9 <= hour <= 17:
                    value = 100 + (hour - 9) * 5  # Peak during day
                else:
                    value = 20 + hour  # Lower at night
                
                values.append(value)
        
        # Should detect pattern with sufficient data
        has_pattern = MetricCalculator.is_seasonal_pattern(values, timestamps, period_hours=24)
        self.assertTrue(has_pattern)
        
        # Test with insufficient data
        short_values = values[:10]
        short_timestamps = timestamps[:10]
        has_pattern_short = MetricCalculator.is_seasonal_pattern(short_values, short_timestamps)
        self.assertFalse(has_pattern_short)

class TestCostCalculator(unittest.TestCase):
    """Test cases for CostCalculator class"""
    
    def test_estimate_lambda_cost(self):
        """Test Lambda cost estimation"""
        cost_breakdown = CostCalculator.estimate_lambda_cost(
            invocations=1000000,  # 1M invocations
            avg_duration_ms=500,  # 500ms average
            memory_mb=512,        # 512MB memory
            days=30
        )
        
        self.assertIn('request_cost', cost_breakdown)
        self.assertIn('duration_cost', cost_breakdown)
        self.assertIn('total_cost', cost_breakdown)
        self.assertIn('monthly_estimate', cost_breakdown)
        
        # Request cost should be positive
        self.assertGreater(cost_breakdown['request_cost'], 0)
        
        # Duration cost should be positive
        self.assertGreater(cost_breakdown['duration_cost'], 0)
        
        # Total should equal sum of components
        expected_total = cost_breakdown['request_cost'] + cost_breakdown['duration_cost']
        self.assertAlmostEqual(cost_breakdown['total_cost'], expected_total, places=6)
    
    def test_estimate_monitoring_cost(self):
        """Test monitoring cost estimation"""
        cost_breakdown = CostCalculator.estimate_monitoring_cost(
            num_metrics=100,
            num_alarms=50,
            log_volume_gb=10.0
        )
        
        self.assertIn('metrics_cost', cost_breakdown)
        self.assertIn('alarms_cost', cost_breakdown)
        self.assertIn('logs_ingestion_cost', cost_breakdown)
        self.assertIn('logs_storage_cost', cost_breakdown)
        self.assertIn('total_monthly_cost', cost_breakdown)
        
        # All costs should be positive
        for cost_type, cost_value in cost_breakdown.items():
            self.assertGreaterEqual(cost_value, 0)
        
        # Total should equal sum of components
        expected_total = (
            cost_breakdown['metrics_cost'] +
            cost_breakdown['alarms_cost'] +
            cost_breakdown['logs_ingestion_cost'] +
            cost_breakdown['logs_storage_cost']
        )
        self.assertAlmostEqual(cost_breakdown['total_monthly_cost'], expected_total, places=6)

if __name__ == '__main__':
    unittest.main()