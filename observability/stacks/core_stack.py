from aws_cdk import (
    Stack,
    aws_iam as iam,
    aws_logs as logs,
    aws_s3 as s3,
    aws_kms as kms,
    aws_events as events,
    aws_xray as xray,
    RemovalPolicy,
    Duration
)
from constructs import Construct
from typing import Dict, Any

class CoreObservabilityStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, environment: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        self.env_name = environment
        self.core_resources = {}
        
        # Create core resources
        self._create_encryption_key()
        self._create_storage_bucket()
        self._create_log_groups()
        self._create_iam_roles()
        self._create_event_bus()
        self._create_xray_resources()
    
    def _create_encryption_key(self):
        """Create KMS key for encrypting observability data"""
        self.core_resources["kms_key"] = kms.Key(
            self, "ObservabilityKey",
            description=f"Observability platform encryption key - {self.env_name}",
            enable_key_rotation=True,
            removal_policy=RemovalPolicy.DESTROY if self.env_name == "dev" else RemovalPolicy.RETAIN
        )
        
        kms.Alias(
            self, "ObservabilityKeyAlias",
            alias_name=f"alias/observability-{self.env_name}",
            target_key=self.core_resources["kms_key"]
        )
    
    def _create_storage_bucket(self):
        """Create S3 bucket for storing observability data"""
        self.core_resources["storage_bucket"] = s3.Bucket(
            self, "ObservabilityBucket",
            encryption=s3.BucketEncryption.KMS,
            encryption_key=self.core_resources["kms_key"],
            versioned=True,
            lifecycle_rules=[
                s3.LifecycleRule(
                    id="ArchiveOldData",
                    enabled=True,
                    transitions=[
                        s3.Transition(
                            storage_class=s3.StorageClass.INFREQUENT_ACCESS,
                            transition_after=Duration.days(30)
                        ),
                        s3.Transition(
                            storage_class=s3.StorageClass.GLACIER,
                            transition_after=Duration.days(90)
                        )
                    ],
                    expiration=Duration.days(365)
                )
            ],
            removal_policy=RemovalPolicy.DESTROY if self.env_name == "dev" else RemovalPolicy.RETAIN
        )
    
    def _create_log_groups(self):
        """Create CloudWatch log groups for the platform"""
        log_groups = {
            "platform_logs": "/observability/platform",
            "metric_collector_logs": "/observability/metric-collector",
            "alert_processor_logs": "/observability/alert-processor",
            "automation_logs": "/observability/automation",
            "cost_monitor_logs": "/observability/cost-monitor"
        }
        
        self.core_resources["log_groups"] = {}
        for name, log_group_name in log_groups.items():
            self.core_resources["log_groups"][name] = logs.LogGroup(
                self, f"LogGroup{name.title().replace('_', '')}",
                log_group_name=log_group_name,
                retention=logs.RetentionDays.ONE_MONTH if self.env_name == "dev" else logs.RetentionDays.SIX_MONTHS,
                encryption_key=self.core_resources["kms_key"],
                removal_policy=RemovalPolicy.DESTROY
            )
    
    def _create_iam_roles(self):
        """Create IAM roles for observability functions"""
        # Lambda execution role with observability permissions
        self.core_resources["lambda_role"] = iam.Role(
            self, "ObservabilityLambdaRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole"),
                iam.ManagedPolicy.from_aws_managed_policy_name("AWSXRayDaemonWriteAccess")
            ],
            inline_policies={
                "ObservabilityPolicy": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=[
                                "cloudwatch:*",
                                "logs:*",
                                "events:*",
                                "sns:*",
                                "s3:GetObject",
                                "s3:PutObject",
                                "s3:DeleteObject",
                                "kms:Decrypt",
                                "kms:Encrypt",
                                "kms:GenerateDataKey",
                                "ec2:Describe*",
                                "ecs:Describe*",
                                "rds:Describe*",
                                "lambda:List*",
                                "lambda:Get*",
                                "budgets:ViewBudget",
                                "ce:GetCostAndUsage",
                                "ce:GetUsageReport"
                            ],
                            resources=["*"]
                        )
                    ]
                )
            }
        )
        
        # EventBridge role for cross-service communication
        self.core_resources["eventbridge_role"] = iam.Role(
            self, "ObservabilityEventBridgeRole",
            assumed_by=iam.ServicePrincipal("events.amazonaws.com"),
            inline_policies={
                "EventBridgePolicy": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=[
                                "lambda:InvokeFunction",
                                "sns:Publish",
                                "logs:CreateLogStream",
                                "logs:PutLogEvents"
                            ],
                            resources=["*"]
                        )
                    ]
                )
            }
        )
    
    def _create_event_bus(self):
        """Create custom EventBridge bus for observability events"""
        self.core_resources["event_bus"] = events.EventBus(
            self, "ObservabilityEventBus"
        )
        
        # Archive events for replay capability
        events.Archive(
            self, "ObservabilityEventArchive",
            source_event_bus=self.core_resources["event_bus"],
            description="Archive of observability events for replay",
            event_pattern=events.EventPattern(
                source=["observability.platform"]
            ),
            retention=Duration.days(30)
        )
    
    def _create_xray_resources(self):
        """Create X-Ray tracing resources"""
        # X-Ray tracing will be enabled at the Lambda function level
        pass