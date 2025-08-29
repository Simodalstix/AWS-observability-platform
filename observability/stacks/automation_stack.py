from aws_cdk import (
    Stack,
    aws_lambda as lambda_,
    aws_events as events,
    aws_events_targets as targets,
    aws_stepfunctions as sfn,
    aws_stepfunctions_tasks as tasks,
    aws_iam as iam,
    Duration
)
from constructs import Construct
from typing import Dict, Any

class AutomationStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, environment: str, 
                 core_resources: Dict[str, Any], alerting_resources: Dict[str, Any], **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        self.env_name = environment
        self.core_resources = core_resources
        self.alerting_resources = alerting_resources
        self.automation_resources = {}
        
        # Create automation components
        self._create_automation_role()
        self._create_remediation_functions()
        self._create_remediation_workflows()
        self._create_incident_response()
    
    def _create_automation_role(self):
        """Create IAM role for automation functions"""
        self.automation_role = iam.Role(
            self, "AutomationRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole"),
                iam.ManagedPolicy.from_aws_managed_policy_name("AWSXRayDaemonWriteAccess")
            ],
            inline_policies={
                "AutomationPolicy": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=[
                                "ec2:RebootInstances",
                                "ec2:DescribeInstances",
                                "lambda:UpdateFunctionConfiguration",
                                "lambda:GetFunction",
                                "ecs:UpdateService",
                                "ecs:DescribeServices",
                                "cloudwatch:PutMetricData",
                                "stepfunctions:StartExecution",
                                "sns:Publish"
                            ],
                            resources=["*"]
                        )
                    ]
                )
            }
        )
    
    def _create_remediation_functions(self):
        """Create Lambda functions for automated remediation"""
        
        # EC2 instance restart function
        self.automation_resources["ec2_restart"] = lambda_.Function(
            self, "EC2RestartFunction",
            runtime=lambda_.Runtime.PYTHON_3_9,
            handler="index.handler",
            code=lambda_.Code.from_inline("def handler(event, context): return {'statusCode': 200}"),
            role=self.automation_role,
            timeout=Duration.minutes(2),
            tracing=lambda_.Tracing.ACTIVE
        )
        
        # Lambda function restart function
        self.automation_resources["lambda_restart"] = lambda_.Function(
            self, "LambdaRestartFunction",
            runtime=lambda_.Runtime.PYTHON_3_9,
            handler="index.handler",
            code=lambda_.Code.from_inline("def handler(event, context): return {'statusCode': 200}"),
            role=self.automation_role,
            timeout=Duration.minutes(2),
            tracing=lambda_.Tracing.ACTIVE
        )
        
        # ECS service scaling function
        self.automation_resources["ecs_scale"] = lambda_.Function(
            self, "ECSScaleFunction",
            runtime=lambda_.Runtime.PYTHON_3_9,
            handler="index.handler",
            code=lambda_.Code.from_inline("def handler(event, context): return {'statusCode': 200}"),
            role=self.automation_role,
            timeout=Duration.minutes(2),
            tracing=lambda_.Tracing.ACTIVE
        )
    
    def _create_remediation_workflows(self):
        """Create Step Functions workflows for complex remediation"""
        
        # Define remediation workflow
        check_health = tasks.LambdaInvoke(
            self, "CheckHealth",
            lambda_function=self.automation_resources["ec2_restart"],
            payload=sfn.TaskInput.from_object({
                "action": "check_health",
                "resource_id.$": "$.resource_id"
            })
        )
        
        restart_resource = tasks.LambdaInvoke(
            self, "RestartResource",
            lambda_function=self.automation_resources["ec2_restart"],
            payload=sfn.TaskInput.from_object({
                "action": "restart",
                "resource_id.$": "$.resource_id"
            })
        )
        
        wait_for_recovery = sfn.Wait(
            self, "WaitForRecovery",
            time=sfn.WaitTime.duration(Duration.minutes(2))
        )
        
        verify_recovery = tasks.LambdaInvoke(
            self, "VerifyRecovery",
            lambda_function=self.automation_resources["ec2_restart"],
            payload=sfn.TaskInput.from_object({
                "action": "verify",
                "resource_id.$": "$.resource_id"
            })
        )
        
        success_state = sfn.Succeed(self, "RemediationSuccess")
        failure_state = sfn.Fail(self, "RemediationFailed")
        
        # Define workflow
        definition = check_health.next(
            sfn.Choice(self, "IsHealthy")
            .when(
                sfn.Condition.string_equals("$.status", "healthy"),
                success_state
            )
            .otherwise(
                restart_resource.next(
                    wait_for_recovery.next(
                        verify_recovery.next(
                            sfn.Choice(self, "IsRecovered")
                            .when(
                                sfn.Condition.string_equals("$.status", "healthy"),
                                success_state
                            )
                            .otherwise(failure_state)
                        )
                    )
                )
            )
        )
        
        self.automation_resources["remediation_workflow"] = sfn.StateMachine(
            self, "RemediationWorkflow",
            state_machine_name=f"observability-remediation-{self.env_name}",
            definition=definition,
            timeout=Duration.minutes(15)
        )
    
    def _create_incident_response(self):
        """Create incident response automation"""
        
        # Incident response orchestrator
        incident_responder = lambda_.Function(
            self, "IncidentResponder",
            runtime=lambda_.Runtime.PYTHON_3_9,
            handler="index.handler",
            code=lambda_.Code.from_inline("def handler(event, context): return {'statusCode': 200}"),
            role=self.automation_role,
            timeout=Duration.minutes(2),
            tracing=lambda_.Tracing.ACTIVE,
            environment={
                "REMEDIATION_WORKFLOW_ARN": self.automation_resources["remediation_workflow"].state_machine_arn,
                "INCIDENT_TOPIC_ARN": self.alerting_resources["topics"]["critical"].topic_arn
            }
        )
        
        # Subscribe to alert events
        events.Rule(
            self, "IncidentResponseRule",
            event_bus=self.core_resources["event_bus"],
            event_pattern=events.EventPattern(
                source=["observability.alerts"],
                detail_type=["Alert Processed"],
                detail={
                    "severity": ["critical", "high"]
                }
            ),
            targets=[targets.LambdaFunction(incident_responder)]
        )