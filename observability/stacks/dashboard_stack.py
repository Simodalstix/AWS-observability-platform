from aws_cdk import (
    Stack,
    aws_cloudwatch as cloudwatch
)
from constructs import Construct
from typing import Dict, Any

class DashboardStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, environment: str, core_resources: Dict[str, Any], **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        self.env_name = environment
        self.core_resources = core_resources
        
        # Create simple dashboards
        self._create_overview_dashboard()
        self._create_service_dashboards()
    
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
                ]
            ]
        )
    
    def _create_service_dashboards(self):
        """Create simple service dashboards"""
        # Simple EC2 dashboard
        cloudwatch.Dashboard(
            self, "EC2Dashboard",
            dashboard_name=f"Observability-EC2-{self.env_name}",
            widgets=[[
                cloudwatch.GraphWidget(
                    title="EC2 CPU Utilization",
                    left=[cloudwatch.Metric(
                        namespace="AWS/EC2",
                        metric_name="CPUUtilization",
                        statistic="Average"
                    )],
                    width=24,
                    height=6
                )
            ]]
        )
    
