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
        
        self.environment = environment
        self.core_resources = core_resources
        self.alerting_resources = alerting_resources
        self.automation_resources = {}
        
        # Create automation components
        self._create_automation_role()
        self._create_remediation_functions()
        self._create_remediation_workflows()
        self._create_incident_response()
    
    def _create_remediation_functions(self):
        """Create Lambda functions for automated remediation"""
        
        # EC2 instance restart function
        self.automation_resources["ec2_restart"] = lambda_.Function(
            self, "EC2RestartFunction",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="ec2_remediation.restart_instance",
            code=lambda_.Code.from_inline("""
import boto3
import json
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

ec2 = boto3.client('ec2')
cloudwatch = boto3.client('cloudwatch')

def restart_instance(event, context):
    try:
        instance_id = event.get('instance_id')
        if not instance_id:
            raise ValueError("No instance_id provided")
        
        # Check instance state
        response = ec2.describe_instances(InstanceIds=[instance_id])
        instance = response['Reservations'][0]['Instances'][0]
        
        if instance['State']['Name'] != 'running':
            logger.info(f"Instance {instance_id} is not running, skipping restart")
            return {'status': 'skipped', 'reason': 'instance_not_running'}
        
        # Restart instance
        ec2.reboot_instances(InstanceIds=[instance_id])
        
        # Send custom metric
        cloudwatch.put_metric_data(
            Namespace='Observability/Automation',
            MetricData=[
                {
                    'MetricName': 'InstanceRestart',
                    'Value': 1,
                    'Dimensions': [
                        {'Name': 'InstanceId', 'Value': instance_id}
                    ]
                }
            ]
        )
        
        logger.info(f"Successfully restarted instance {instance_id}")
        return {'status': 'success', 'instance_id': instance_id}
        
    except Exception as e:
        logger.error(f"Error restarting instance: {str(e)}")
        return {'status': 'error', 'error': str(e)}
"""),
            role=self._create_automation_role(),
            timeout=Duration.minutes(2),
            log_group=self.core_resources["log_groups"]["automation_logs"],
            tracing=lambda_.Tracing.ACTIVE
        )
        
        # Lambda function restart function
        self.automation_resources["lambda_restart"] = lambda_.Function(
            self, "LambdaRestartFunction",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="lambda_remediation.restart_function",
            code=lambda_.Code.from_inline("""
import boto3
import json
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

lambda_client = boto3.client('lambda')
cloudwatch = boto3.client('cloudwatch')

def restart_function(event, context):
    try:
        function_name = event.get('function_name')
        if not function_name:
            raise ValueError("No function_name provided")
        
        # Update function configuration to trigger restart
        lambda_client.update_function_configuration(
            FunctionName=function_name,
            Environment={
                'Variables': {
                    'RESTART_TIMESTAMP': str(context.aws_request_id)
                }
            }
        )
        
        # Send custom metric
        cloudwatch.put_metric_data(
            Namespace='Observability/Automation',
            MetricData=[
                {
                    'MetricName': 'LambdaRestart',
                    'Value': 1,
                    'Dimensions': [
                        {'Name': 'FunctionName', 'Value': function_name}
                    ]
                }
            ]
        )
        
        logger.info(f"Successfully triggered restart for function {function_name}")
        return {'status': 'success', 'function_name': function_name}
        
    except Exception as e:
        logger.error(f"Error restarting function: {str(e)}")
        return {'status': 'error', 'error': str(e)}
"""),
            role=self._create_automation_role(),
            timeout=Duration.minutes(2),
            log_group=self.core_resources["log_groups"]["automation_logs"],
            tracing=lambda_.Tracing.ACTIVE
        )
        
        # ECS service scaling function
        self.automation_resources["ecs_scale"] = lambda_.Function(
            self, "ECSScaleFunction",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="ecs_remediation.scale_service",
            code=lambda_.Code.from_inline("""
import boto3
import json
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

ecs = boto3.client('ecs')
cloudwatch = boto3.client('cloudwatch')

def scale_service(event, context):
    try:
        cluster_name = event.get('cluster_name')
        service_name = event.get('service_name')
        desired_count = event.get('desired_count', 2)
        
        if not cluster_name or not service_name:
            raise ValueError("cluster_name and service_name are required")
        
        # Update service
        ecs.update_service(
            cluster=cluster_name,
            service=service_name,
            desiredCount=desired_count
        )
        
        # Send custom metric
        cloudwatch.put_metric_data(
            Namespace='Observability/Automation',
            MetricData=[
                {
                    'MetricName': 'ECSServiceScale',
                    'Value': desired_count,
                    'Dimensions': [
                        {'Name': 'ClusterName', 'Value': cluster_name},
                        {'Name': 'ServiceName', 'Value': service_name}
                    ]
                }
            ]
        )
        
        logger.info(f"Successfully scaled service {service_name} to {desired_count}")
        return {'status': 'success', 'service_name': service_name, 'desired_count': desired_count}
        
    except Exception as e:
        logger.error(f"Error scaling service: {str(e)}")
        return {'status': 'error', 'error': str(e)}
"""),
            role=self._create_automation_role(),
            timeout=Duration.minutes(2),
            log_group=self.core_resources["log_groups"]["automation_logs"],
            tracing=lambda_.Tracing.ACTIVE
        )
    
    def _create_automation_role(self):
        """Create IAM role for automation functions"""
        return iam.Role(
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
                                "logs:CreateLogGroup",
                                "logs:CreateLogStream",
                                "logs:PutLogEvents"
                            ],
                            resources=["*"]
                        )
                    ]
                )
            }
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
            state_machine_name=f"observability-remediation-{self.environment}",
            definition=definition,
            timeout=Duration.minutes(15)
        )
    
    def _create_auto_scaling_automation(self):
        """Create auto-scaling automation based on metrics"""
        
        # Auto-scaling function
        auto_scaler = lambda_.Function(
            self, "AutoScaler",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="auto_scaler.handler",
            code=lambda_.Code.from_inline("""
import boto3
import json
import logging
from datetime import datetime, timedelta

logger = logging.getLogger()
logger.setLevel(logging.INFO)

cloudwatch = boto3.client('cloudwatch')
ecs = boto3.client('ecs')
application_autoscaling = boto3.client('application-autoscaling')

def handler(event, context):
    try:
        # Get metric data for scaling decisions
        metric_data = get_scaling_metrics()
        
        # Make scaling decisions
        scaling_actions = determine_scaling_actions(metric_data)
        
        # Execute scaling actions
        for action in scaling_actions:
            execute_scaling_action(action)
        
        return {'statusCode': 200, 'actions': scaling_actions}
        
    except Exception as e:
        logger.error(f"Error in auto-scaling: {str(e)}")
        return {'statusCode': 500, 'error': str(e)}

def get_scaling_metrics():
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(minutes=10)
    
    # Get CPU utilization metrics
    response = cloudwatch.get_metric_statistics(
        Namespace='AWS/ECS',
        MetricName='CPUUtilization',
        Dimensions=[],
        StartTime=start_time,
        EndTime=end_time,
        Period=300,
        Statistics=['Average']
    )
    
    return response['Datapoints']

def determine_scaling_actions(metric_data):
    actions = []
    
    if not metric_data:
        return actions
    
    avg_cpu = sum(point['Average'] for point in metric_data) / len(metric_data)
    
    if avg_cpu > 70:
        actions.append({
            'action': 'scale_up',
            'reason': f'High CPU utilization: {avg_cpu:.2f}%'
        })
    elif avg_cpu < 30:
        actions.append({
            'action': 'scale_down',
            'reason': f'Low CPU utilization: {avg_cpu:.2f}%'
        })
    
    return actions

def execute_scaling_action(action):
    logger.info(f"Executing scaling action: {action}")
    # Implementation would depend on specific scaling targets
    # This is a placeholder for actual scaling logic
"""),
            role=self._create_automation_role(),
            timeout=Duration.minutes(5),
            log_group=self.core_resources["log_groups"]["automation_logs"],
            tracing=lambda_.Tracing.ACTIVE
        )
        
        # Schedule auto-scaling checks
        events.Rule(
            self, "AutoScalingSchedule",
            schedule=events.Schedule.rate(Duration.minutes(5)),
            targets=[targets.LambdaFunction(auto_scaler)]
        )
    
    def _create_incident_response(self):
        """Create incident response automation"""
        
        # Incident response orchestrator
        incident_responder = lambda_.Function(
            self, "IncidentResponder",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="incident_response.handler",
            code=lambda_.Code.from_inline("""
import boto3
import json
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

stepfunctions = boto3.client('stepfunctions')
sns = boto3.client('sns')

def handler(event, context):
    try:
        # Parse alert event
        alert_detail = event.get('detail', {})
        severity = alert_detail.get('severity', 'medium')
        
        # Determine response based on severity
        if severity in ['critical', 'high']:
            # Start automated remediation workflow
            start_remediation_workflow(alert_detail)
            
            # Send immediate notification
            send_incident_notification(alert_detail)
        
        return {'statusCode': 200}
        
    except Exception as e:
        logger.error(f"Error in incident response: {str(e)}")
        return {'statusCode': 500}

def start_remediation_workflow(alert_detail):
    state_machine_arn = os.environ.get('REMEDIATION_WORKFLOW_ARN')
    if state_machine_arn:
        stepfunctions.start_execution(
            stateMachineArn=state_machine_arn,
            input=json.dumps(alert_detail)
        )

def send_incident_notification(alert_detail):
    topic_arn = os.environ.get('INCIDENT_TOPIC_ARN')
    if topic_arn:
        sns.publish(
            TopicArn=topic_arn,
            Message=json.dumps(alert_detail, indent=2),
            Subject=f"INCIDENT: {alert_detail.get('alarm_name', 'Unknown')}"
        )
"""),
            role=self._create_automation_role(),
            timeout=Duration.minutes(2),
            log_group=self.core_resources["log_groups"]["automation_logs"],
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