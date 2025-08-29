from aws_cdk import (
    Stack,
    aws_cloudwatch as cloudwatch,
    aws_lambda as lambda_,
    aws_events as events,
    aws_events_targets as targets,
    Duration
)
from constructs import Construct
from typing import Dict, Any, List
from ..config.monitoring_config import MonitoringConfig

class DashboardStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, environment: str, core_resources: Dict[str, Any], **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        self.env_name = environment
        self.core_resources = core_resources
        
        # Create dashboards
        self._create_overview_dashboard()
        self._create_service_dashboards()
        self._create_dashboard_updater()
    
    def _create_overview_dashboard(self):
        """Create main overview dashboard"""
        self.overview_dashboard = cloudwatch.Dashboard(
            self, "OverviewDashboard",
            dashboard_name=f"Observability-Overview-{self.env_name}",
            widgets=[
                [
                    cloudwatch.GraphWidget(
                        title="Infrastructure Health",
                        left=[
                            cloudwatch.Metric(
                                namespace="AWS/EC2",
                                metric_name="CPUUtilization",
                                statistic="Average"
                            ),
                            cloudwatch.Metric(
                                namespace="AWS/Lambda",
                                metric_name="Duration",
                                statistic="Average"
                            )
                        ],
                        width=12,
                        height=6
                    )
                ],
                [
                    cloudwatch.SingleValueWidget(
                        title="Active Alarms",
                        metrics=[
                            cloudwatch.Metric(
                                namespace="AWS/CloudWatch",
                                metric_name="MetricCount",
                                statistic="Sum"
                            )
                        ],
                        width=6,
                        height=3
                    ),
                    cloudwatch.SingleValueWidget(
                        title="Error Rate",
                        metrics=[
                            cloudwatch.Metric(
                                namespace="AWS/Lambda",
                                metric_name="Errors",
                                statistic="Sum"
                            )
                        ],
                        width=6,
                        height=3
                    )
                ],
                [
                    cloudwatch.LogQueryWidget(
                        title="Recent Errors",
                        query_string="fields @timestamp, @message | filter @message like /ERROR/ | sort @timestamp desc | limit 20",
                        width=24,
                        height=6
                    )
                ]
            ]
        )
    
    def _create_service_dashboards(self):
        """Create service-specific dashboards"""
        services = ["ec2", "lambda", "rds", "ecs"]
        self.service_dashboards = {}
        
        for service in services:
            config = MonitoringConfig.get_service_config(service)
            if not config:
                continue
                
            widgets = []
            
            # Create metric widgets for each service
            for i, metric in enumerate(config.metrics):
                if i % 2 == 0:
                    widgets.append([])
                
                widget = cloudwatch.GraphWidget(
                    title=f"{service.upper()} - {metric.metric_name}",
                    left=[
                        cloudwatch.Metric(
                            namespace=metric.namespace,
                            metric_name=metric.metric_name,
                            statistic=metric.statistic,
                            period=Duration.minutes(metric.period // 60)
                        )
                    ],
                    width=12,
                    height=6
                )
                widgets[-1].append(widget)
            
            # Add log insights widget
            if config.log_groups:
                widgets.append([
                    cloudwatch.LogQueryWidget(
                        title=f"{service.upper()} Logs",
                        query_string="fields @timestamp, @message | sort @timestamp desc | limit 50",
                        width=24,
                        height=8
                    )
                ])
            
            self.service_dashboards[service] = cloudwatch.Dashboard(
                self, f"{service.title()}Dashboard",
                dashboard_name=f"Observability-{service.upper()}-{self.env_name}",
                widgets=widgets
            )
    
    def _create_dashboard_updater(self):
        """Create Lambda function to dynamically update dashboards"""
        dashboard_updater = lambda_.Function(
            self, "DashboardUpdater",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="handler.handler",
            code=lambda_.Code.from_asset("src/lambda/dashboard_updater"),
            role=self.core_resources["lambda_role"],
            timeout=Duration.minutes(5),
            log_group=self.core_resources["log_groups"]["platform_logs"],
            tracing=lambda_.Tracing.ACTIVE
        )
        
        # Schedule dashboard updates
        events.Rule(
            self, "DashboardUpdateSchedule",
            schedule=events.Schedule.rate(Duration.hours(1)),
            targets=[targets.LambdaFunction(dashboard_updater)]
        )