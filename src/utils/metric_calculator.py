"""
Utility functions for metric calculations and analysis
"""
import statistics
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

class MetricCalculator:
    """Utility class for metric calculations and anomaly detection"""
    
    @staticmethod
    def calculate_anomaly_threshold(
        historical_values: List[float], 
        sensitivity: float = 2.0
    ) -> float:
        """
        Calculate anomaly threshold using statistical methods
        
        Args:
            historical_values: List of historical metric values
            sensitivity: Number of standard deviations for threshold
            
        Returns:
            Threshold value for anomaly detection
        """
        if len(historical_values) < 2:
            return 0.0
        
        mean = statistics.mean(historical_values)
        std_dev = statistics.stdev(historical_values)
        
        return mean + (sensitivity * std_dev)
    
    @staticmethod
    def detect_trend(values: List[float], window_size: int = 5) -> str:
        """
        Detect trend in metric values
        
        Args:
            values: List of metric values in chronological order
            window_size: Size of the moving window for trend analysis
            
        Returns:
            Trend direction: 'increasing', 'decreasing', or 'stable'
        """
        if len(values) < window_size:
            return 'stable'
        
        recent_values = values[-window_size:]
        older_values = values[-window_size*2:-window_size] if len(values) >= window_size*2 else values[:-window_size]
        
        if not older_values:
            return 'stable'
        
        recent_avg = statistics.mean(recent_values)
        older_avg = statistics.mean(older_values)
        
        # Calculate percentage change
        change_percent = ((recent_avg - older_avg) / older_avg) * 100 if older_avg != 0 else 0
        
        if change_percent > 10:  # 10% increase
            return 'increasing'
        elif change_percent < -10:  # 10% decrease
            return 'decreasing'
        else:
            return 'stable'
    
    @staticmethod
    def calculate_percentiles(values: List[float]) -> Dict[str, float]:
        """
        Calculate common percentiles for metric values
        
        Args:
            values: List of metric values
            
        Returns:
            Dictionary with percentile values
        """
        if not values:
            return {}
        
        sorted_values = sorted(values)
        
        return {
            'p50': statistics.median(sorted_values),
            'p90': MetricCalculator._percentile(sorted_values, 90),
            'p95': MetricCalculator._percentile(sorted_values, 95),
            'p99': MetricCalculator._percentile(sorted_values, 99)
        }
    
    @staticmethod
    def _percentile(sorted_values: List[float], percentile: float) -> float:
        """Calculate specific percentile from sorted values"""
        if not sorted_values:
            return 0.0
        
        index = (percentile / 100) * (len(sorted_values) - 1)
        
        if index.is_integer():
            return sorted_values[int(index)]
        else:
            lower_index = int(index)
            upper_index = lower_index + 1
            
            if upper_index >= len(sorted_values):
                return sorted_values[-1]
            
            # Linear interpolation
            weight = index - lower_index
            return sorted_values[lower_index] * (1 - weight) + sorted_values[upper_index] * weight
    
    @staticmethod
    def is_seasonal_pattern(
        values: List[float], 
        timestamps: List[datetime],
        period_hours: int = 24
    ) -> bool:
        """
        Detect if there's a seasonal pattern in the data
        
        Args:
            values: List of metric values
            timestamps: Corresponding timestamps
            period_hours: Expected period in hours (default: 24 for daily pattern)
            
        Returns:
            True if seasonal pattern is detected
        """
        if len(values) < period_hours * 2:  # Need at least 2 periods
            return False
        
        # Group values by hour of day (for daily seasonality)
        hourly_groups: Dict[int, List[float]] = {}
        for value, timestamp in zip(values, timestamps):
            hour = timestamp.hour
            if hour not in hourly_groups:
                hourly_groups[hour] = []
            hourly_groups[hour].append(value)
        
        # Calculate coefficient of variation for each hour
        hourly_cv = {}
        for hour, hour_values in hourly_groups.items():
            if len(hour_values) > 1:
                mean_val = statistics.mean(hour_values)
                std_val = statistics.stdev(hour_values)
                hourly_cv[hour] = std_val / mean_val if mean_val != 0 else 0
        
        # If most hours have low coefficient of variation, it suggests seasonality
        if len(hourly_cv) >= 12:  # At least half the day
            low_cv_count = sum(1 for cv in hourly_cv.values() if cv < 0.5)
            return low_cv_count / len(hourly_cv) > 0.6  # 60% of hours have consistent patterns
        
        return False

class CostCalculator:
    """Utility class for cost-related calculations"""
    
    # AWS service pricing (simplified, actual pricing varies by region)
    SERVICE_COSTS = {
        'lambda': {
            'requests': 0.0000002,  # per request
            'duration_gb_second': 0.0000166667  # per GB-second
        },
        'ec2': {
            't3.micro': 0.0104,  # per hour
            't3.small': 0.0208,
            't3.medium': 0.0416,
            't3.large': 0.0832
        },
        'cloudwatch': {
            'metrics': 0.30,  # per metric per month
            'alarms': 0.10,   # per alarm per month
            'logs_ingestion': 0.50,  # per GB
            'logs_storage': 0.03     # per GB per month
        }
    }
    
    @staticmethod
    def estimate_lambda_cost(
        invocations: int,
        avg_duration_ms: float,
        memory_mb: int,
        days: int = 30
    ) -> Dict[str, float]:
        """
        Estimate Lambda function cost
        
        Args:
            invocations: Number of invocations
            avg_duration_ms: Average duration in milliseconds
            memory_mb: Memory allocation in MB
            days: Number of days for calculation
            
        Returns:
            Cost breakdown dictionary
        """
        # Request cost
        request_cost = invocations * CostCalculator.SERVICE_COSTS['lambda']['requests']
        
        # Duration cost
        duration_seconds = (avg_duration_ms / 1000) * invocations
        gb_seconds = (memory_mb / 1024) * duration_seconds
        duration_cost = gb_seconds * CostCalculator.SERVICE_COSTS['lambda']['duration_gb_second']
        
        total_cost = request_cost + duration_cost
        monthly_cost = total_cost * (30 / days)
        
        return {
            'request_cost': request_cost,
            'duration_cost': duration_cost,
            'total_cost': total_cost,
            'monthly_estimate': monthly_cost
        }
    
    @staticmethod
    def estimate_monitoring_cost(
        num_metrics: int,
        num_alarms: int,
        log_volume_gb: float
    ) -> Dict[str, float]:
        """
        Estimate CloudWatch monitoring cost
        
        Args:
            num_metrics: Number of custom metrics
            num_alarms: Number of alarms
            log_volume_gb: Log volume in GB per month
            
        Returns:
            Cost breakdown dictionary
        """
        costs = CostCalculator.SERVICE_COSTS['cloudwatch']
        
        metrics_cost = num_metrics * costs['metrics']
        alarms_cost = num_alarms * costs['alarms']
        logs_ingestion_cost = log_volume_gb * costs['logs_ingestion']
        logs_storage_cost = log_volume_gb * costs['logs_storage']
        
        total_cost = metrics_cost + alarms_cost + logs_ingestion_cost + logs_storage_cost
        
        return {
            'metrics_cost': metrics_cost,
            'alarms_cost': alarms_cost,
            'logs_ingestion_cost': logs_ingestion_cost,
            'logs_storage_cost': logs_storage_cost,
            'total_monthly_cost': total_cost
        }