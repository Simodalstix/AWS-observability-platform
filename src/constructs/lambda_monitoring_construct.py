"""
Lambda-specific monitoring construct
"""
from aws_cdk import (
    aws_lambda as lambda_,
    aws_cloudwatch as cloudwatch,
    aws_cloudwatch_actions as cloudwatch_actions,
    aws_logs as logs,
    Duration
)
from constructs import Construct
from .monitoring_construct import MonitoringConstruct

class LambdaMonitoringConstruct(MonitoringConstruct):
    """
    Specialized monitoring construct for Lambda functions
    Includes Lambda-specific metrics and best practices
    """
    
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        lambda_function: lambda_.Function,
        environment: str,
        **kwargs
    ) -> None:
        
        # Lambda-specific metrics configuration
        lambda_metrics_config = [
            {
                'namespace': 'AWS/Lambda',
                'metric_name': 'Duration',
                'statistic': 'Average',
                'period': 5,
                'alarm': {
                    'threshold': 10000,  # 10 seconds
                    'description': 'Lambda function duration is too high',
                    'comparison_operator': 'GREATER_THAN_THRESHOLD'
                }
            },
            {
                'namespace': 'AWS/Lambda',
                'metric_name': 'Errors',
                'statistic': 'Sum',
                'period': 5,
                'alarm': {
                    'threshold': 5,
                    'description': 'Lambda function error rate is too high',
                    'comparison_operator': 'GREATER_THAN_THRESHOLD'
                }
            },
            {
                'namespace': 'AWS/Lambda',
                'metric_name': 'Throttles',
                'statistic': 'Sum',
                'period': 5,
                'alarm': {
                    'threshold': 1,
                    'description': 'Lambda function is being throttled',
                    'comparison_operator': 'GREATER_THAN_OR_EQUAL_TO_THRESHOLD'
                }
            },
            {
                'namespace': 'AWS/Lambda',
                'metric_name': 'ConcurrentExecutions',
                'statistic': 'Maximum',
                'period': 5
            }
        ]
        
        super().__init__(
            scope,
            construct_id,
            service_name=f"Lambda-{lambda_function.function_name}",
            environment=environment,
            metrics_config=lambda_metrics_config,
            **kwargs
        )
        
        self.lambda_function = lambda_function
        
        # Add Lambda-specific monitoring
        self._create_log_insights_queries()
        self._create_custom_metrics()
    
    def _create_log_insights_queries(self):
        """Create CloudWatch Logs Insights queries for Lambda"""
        # This would create saved queries for common Lambda troubleshooting
        pass
    
    def _create_custom_metrics(self):
        """Create custom metrics specific to Lambda monitoring"""
        # Add cold start detection
        cold_start_alarm = cloudwatch.Alarm(
            self, "ColdStartAlarm",
            alarm_name=f"{self.lambda_function.function_name}-cold-starts-{self.environment}",
            alarm_description="High number of cold starts detected",
            metric=cloudwatch.Metric(
                namespace="AWS/Lambda",
                metric_name="Duration",
                dimensions_map={
                    "FunctionName": self.lambda_function.function_name
                },
                statistic="Maximum"
            ),
            threshold=5000,  # 5 seconds
            evaluation_periods=3,
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD
        )
        
        if self.alert_topic:
            cold_start_alarm.add_alarm_action(
                cloudwatch_actions.SnsAction(self.alert_topic)
            )