from aws_cdk import (
    Stack,
    aws_budgets as budgets,
    aws_lambda as lambda_,
    aws_events as events,
    aws_events_targets as targets,
    aws_cloudwatch as cloudwatch,
    Duration
)
from constructs import Construct
from typing import Dict, Any

class CostMonitoringStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, environment: str, core_resources: Dict[str, Any], **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        self.env_name = environment
        self.core_resources = core_resources
        self.cost_resources = {}
        
        # Create cost monitoring components
        self._create_budgets()
        self._create_cost_anomaly_detector()
        self._create_cost_dashboard()
    
    def _create_budgets(self):
        """Create AWS Budgets for cost monitoring"""
        
        # Simple monthly budget
        budgets.CfnBudget(
            self, "MonthlyBudget",
            budget=budgets.CfnBudget.BudgetDataProperty(
                budget_type="COST",
                time_unit="MONTHLY",
                budget_limit=budgets.CfnBudget.SpendProperty(
                    amount=1000 if self.env_name == "prod" else 100,
                    unit="USD"
                )
            ),
            notifications_with_subscribers=[
                budgets.CfnBudget.NotificationWithSubscribersProperty(
                    notification=budgets.CfnBudget.NotificationProperty(
                        notification_type="ACTUAL",
                        comparison_operator="GREATER_THAN",
                        threshold=80,
                        threshold_type="PERCENTAGE"
                    ),
                    subscribers=[
                        budgets.CfnBudget.SubscriberProperty(
                            subscription_type="EMAIL",
                            address="admin@example.com"
                        )
                    ]
                )
            ]
        )
    
    def _create_cost_anomaly_detector(self):
        """Create cost anomaly detection"""
        
        cost_anomaly_function = lambda_.Function(
            self, "CostAnomalyDetector",
            runtime=lambda_.Runtime.PYTHON_3_9,
            handler="index.handler",
            code=lambda_.Code.from_inline("def handler(event, context): return {'statusCode': 200}"),
            role=self.core_resources["lambda_role"],
            timeout=Duration.minutes(5),
            tracing=lambda_.Tracing.ACTIVE
        )
        
        # Schedule cost anomaly detection
        events.Rule(
            self, "CostAnomalySchedule",
            schedule=events.Schedule.rate(Duration.hours(6)),
            targets=[targets.LambdaFunction(cost_anomaly_function)]
        )
        
        self.cost_resources["anomaly_detector"] = cost_anomaly_function
    
    def _create_cost_dashboard(self):
        """Create cost monitoring dashboard"""
        
        self.cost_resources["dashboard"] = cloudwatch.Dashboard(
            self, "CostDashboard",
            widgets=[
                [
                    cloudwatch.GraphWidget(
                        title="Daily Cost Trend",
                        left=[
                            cloudwatch.Metric(
                                namespace="AWS/Billing",
                                metric_name="EstimatedCharges",
                                statistic="Maximum"
                            )
                        ],
                        width=24,
                        height=6
                    )
                ]
            ]
        )