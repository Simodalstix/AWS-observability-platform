from aws_cdk import (
    Stack,
    aws_cloudwatch as cloudwatch,
    aws_cloudwatch_actions as cw_actions,
    aws_sns as sns,
    aws_sns_subscriptions as subscriptions,
    aws_lambda as lambda_,
    aws_events as events,
    aws_events_targets as targets,
    aws_ssm as ssm,
    Duration
)
from constructs import Construct
from typing import Dict, Any
# from ..config.monitoring_config import MonitoringConfig

class AlertingStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, environment: str, core_resources: Dict[str, Any], **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        self.env_name = environment
        self.core_resources = core_resources
        self.alerting_resources = {}
        
        # Create alerting infrastructure
        self._create_notification_topics()
        self._create_alert_processor()
        self._create_default_alarms()
        self._create_composite_alarms()
    
    def _create_notification_topics(self):
        """Create SNS topics for different alert severities"""
        severities = ["critical", "high", "medium", "low"]
        self.alerting_resources["topics"] = {}
        
        for severity in severities:
            topic = sns.Topic(
                self, f"AlertTopic{severity.title()}",
                display_name=f"Observability {severity.title()} Alerts",
                master_key=self.core_resources["kms_key"]
            )
            
            # Add email subscription (will be confirmed manually)
            # In production, you'd get this from SSM Parameter or context
            email = self.node.try_get_context("alert_email")
            if email:
                subscriptions.EmailSubscription(email)
            
            self.alerting_resources["topics"][severity] = topic
        
        # Store topic ARNs in SSM for external access
        for severity, topic in self.alerting_resources["topics"].items():
            ssm.StringParameter(
                self, f"AlertTopicArn{severity.title()}",
                parameter_name=f"/observability/{self.env_name}/alerts/topics/{severity}",
                string_value=topic.topic_arn
            )
    
    def _create_alert_processor(self):
        """Create Lambda function to process and enrich alerts"""
        self.alerting_resources["processor"] = lambda_.Function(
            self, "AlertProcessor",
            runtime=lambda_.Runtime.PYTHON_3_9,
            handler="index.handler",
            code=lambda_.Code.from_inline("def handler(event, context): return {'statusCode': 200}"),
            role=self.core_resources["lambda_role"],
            timeout=Duration.minutes(2),
            tracing=lambda_.Tracing.ACTIVE,
            environment={
                "ENVIRONMENT": self.env_name,
                "EVENT_BUS_NAME": self.core_resources["event_bus"].event_bus_name,
                **{f"TOPIC_ARN_{sev.upper()}": topic.topic_arn 
                   for sev, topic in self.alerting_resources["topics"].items()}
            }
        )
        
        # Subscribe processor to CloudWatch alarm state changes
        events.Rule(
            self, "CloudWatchAlarmRule",
            event_pattern=events.EventPattern(
                source=["aws.cloudwatch"],
                detail_type=["CloudWatch Alarm State Change"]
            ),
            targets=[targets.LambdaFunction(self.alerting_resources["processor"])]
        )
        
        # Subscribe to custom EventBridge events
        events.Rule(
            self, "CustomAlertRule",
            event_bus=self.core_resources["event_bus"],
            event_pattern=events.EventPattern(
                source=["observability.custom"],
                detail_type=["Custom Metric Alert"]
            ),
            targets=[targets.LambdaFunction(self.alerting_resources["processor"])]
        )
    
    def _create_default_alarms(self):
        """Create default alarms for common scenarios"""
        self.alerting_resources["alarms"] = {}
        
        # High Lambda error rate alarm
        lambda_error_alarm = cloudwatch.Alarm(
            self, "LambdaHighErrorRate",
            alarm_name=f"observability-lambda-high-errors-{self.env_name}",
            alarm_description="Lambda functions experiencing high error rates",
            metric=cloudwatch.Metric(
                namespace="AWS/Lambda",
                metric_name="Errors",
                statistic="Sum",
                period=Duration.minutes(5)
            ),
            threshold=10,
            evaluation_periods=2,
            datapoints_to_alarm=2,
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
            treat_missing_data=cloudwatch.TreatMissingData.NOT_BREACHING
        )
        
        lambda_error_alarm.add_alarm_action(
            cw_actions.SnsAction(self.alerting_resources["topics"]["high"])
        )
        
        # High EC2 CPU utilization
        ec2_cpu_alarm = cloudwatch.Alarm(
            self, "EC2HighCPU",
            alarm_name=f"observability-ec2-high-cpu-{self.env_name}",
            alarm_description="EC2 instances with high CPU utilization",
            metric=cloudwatch.Metric(
                namespace="AWS/EC2",
                metric_name="CPUUtilization",
                statistic="Average",
                period=Duration.minutes(5)
            ),
            threshold=80,
            evaluation_periods=3,
            datapoints_to_alarm=2,
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD
        )
        
        ec2_cpu_alarm.add_alarm_action(
            cw_actions.SnsAction(self.alerting_resources["topics"]["medium"])
        )
        
        self.alerting_resources["alarms"]["lambda_errors"] = lambda_error_alarm
        self.alerting_resources["alarms"]["ec2_cpu"] = ec2_cpu_alarm
    
    def _create_composite_alarms(self):
        """Create composite alarms for system-wide health"""
        # Composite alarms removed for now - can be added back with correct CDK syntax
        pass