"""
Reusable monitoring construct following AWS CDK best practices
"""
from aws_cdk import (
    aws_cloudwatch as cloudwatch,
    aws_cloudwatch_actions as cw_actions,
    aws_sns as sns,
    Duration
)
from constructs import Construct
from typing import List, Dict, Any, Optional

class MonitoringConstruct(Construct):
    """
    Reusable construct for creating monitoring resources
    Follows AWS Well-Architected Framework principles
    """
    
    def __init__(
        self, 
        scope: Construct, 
        construct_id: str,
        service_name: str,
        environment: str,
        alert_topic: sns.Topic,
        metrics_config: List[Dict[str, Any]],
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        self.service_name = service_name
        self.environment = environment
        self.alert_topic = alert_topic
        
        # Create monitoring resources
        self.dashboard = self._create_dashboard(metrics_config)
        self.alarms = self._create_alarms(metrics_config)
    
    def _create_dashboard(self, metrics_config: List[Dict[str, Any]]) -> cloudwatch.Dashboard:
        """Create service-specific dashboard"""
        widgets: List[List[cloudwatch.IWidget]] = []
        
        # Create widgets based on metrics configuration
        for i, metric_config in enumerate(metrics_config):
            if i % 2 == 0:
                widgets.append([])
            
            widget = cloudwatch.GraphWidget(
                title=f"{self.service_name} - {metric_config['metric_name']}",
                left=[
                    cloudwatch.Metric(
                        namespace=metric_config['namespace'],
                        metric_name=metric_config['metric_name'],
                        statistic=metric_config.get('statistic', 'Average'),
                        period=Duration.minutes(metric_config.get('period', 5))
                    )
                ],
                width=12,
                height=6
            )
            widgets[-1].append(widget)
        
        return cloudwatch.Dashboard(
            self, f"{self.service_name}Dashboard",
            dashboard_name=f"Monitoring-{self.service_name}-{self.environment}",
            widgets=widgets
        )
    
    def _create_alarms(self, metrics_config: List[Dict[str, Any]]) -> List[cloudwatch.Alarm]:
        """Create alarms based on metrics configuration"""
        alarms = []
        
        for metric_config in metrics_config:
            alarm_config = metric_config.get('alarm')
            if not alarm_config:
                continue
            
            alarm = cloudwatch.Alarm(
                self, f"{self.service_name}{metric_config['metric_name']}Alarm",
                alarm_name=f"{self.service_name}-{metric_config['metric_name']}-{self.environment}",
                alarm_description=alarm_config.get('description', f"Alarm for {metric_config['metric_name']}"),
                metric=cloudwatch.Metric(
                    namespace=metric_config['namespace'],
                    metric_name=metric_config['metric_name'],
                    statistic=metric_config.get('statistic', 'Average'),
                    period=Duration.minutes(metric_config.get('period', 5))
                ),
                threshold=alarm_config['threshold'],
                evaluation_periods=alarm_config.get('evaluation_periods', 2),
                datapoints_to_alarm=alarm_config.get('datapoints_to_alarm', 2),
                comparison_operator=getattr(
                    cloudwatch.ComparisonOperator, 
                    alarm_config.get('comparison_operator', 'GREATER_THAN_THRESHOLD')
                ),
                treat_missing_data=cloudwatch.TreatMissingData.NOT_BREACHING
            )
            
            # Add SNS action
            alarm.add_alarm_action(cw_actions.SnsAction(self.alert_topic))
            alarms.append(alarm)
        
        return alarms
    
    def add_custom_metric(
        self, 
        metric_name: str, 
        namespace: str, 
        threshold: float,
        comparison_operator: str = "GREATER_THAN_THRESHOLD"
    ) -> cloudwatch.Alarm:
        """Add a custom metric alarm"""
        alarm = cloudwatch.Alarm(
            self, f"Custom{metric_name}Alarm",
            alarm_name=f"{self.service_name}-{metric_name}-{self.environment}",
            metric=cloudwatch.Metric(
                namespace=namespace,
                metric_name=metric_name,
                statistic="Average"
            ),
            threshold=threshold,
            evaluation_periods=2,
            comparison_operator=getattr(cloudwatch.ComparisonOperator, comparison_operator)
        )
        
        alarm.add_alarm_action(cw_actions.SnsAction(self.alert_topic))
        return alarm