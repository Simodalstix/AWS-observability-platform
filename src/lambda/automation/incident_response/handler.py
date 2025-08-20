"""
Incident response Lambda function
"""
import boto3
import json
import logging
import os

logger = logging.getLogger()
logger.setLevel(logging.INFO)

stepfunctions = boto3.client('stepfunctions')
sns = boto3.client('sns')

def handler(event, context):
    """Handle incident response"""
    try:
        alert_detail = event.get('detail', {})
        severity = alert_detail.get('severity', 'medium')
        
        if severity in ['critical', 'high']:
            start_remediation_workflow(alert_detail)
            send_incident_notification(alert_detail)
        
        return {'statusCode': 200}
        
    except Exception as e:
        logger.error(f"Error in incident response: {str(e)}")
        return {'statusCode': 500}

def start_remediation_workflow(alert_detail):
    """Start automated remediation workflow"""
    workflow_arn = os.environ.get('REMEDIATION_WORKFLOW_ARN')
    if workflow_arn:
        try:
            stepfunctions.start_execution(
                stateMachineArn=workflow_arn,
                input=json.dumps(alert_detail)
            )
            logger.info("Started remediation workflow")
        except Exception as e:
            logger.error(f"Failed to start workflow: {e}")

def send_incident_notification(alert_detail):
    """Send incident notification"""
    topic_arn = os.environ.get('INCIDENT_TOPIC_ARN')
    if topic_arn:
        try:
            sns.publish(
                TopicArn=topic_arn,
                Message=json.dumps(alert_detail, indent=2),
                Subject=f"INCIDENT: {alert_detail.get('alarm_name', 'Unknown')}"
            )
            logger.info("Sent incident notification")
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")