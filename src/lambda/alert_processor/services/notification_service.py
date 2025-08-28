"""
Notification service for sending alerts
"""
import os
import json
import boto3
import logging
from typing import Dict, Any
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

class NotificationService:
    """Service for sending alert notifications"""
    
    def __init__(self):
        self.sns = boto3.client('sns')
        self.events = boto3.client('events')
        self.topic_arns = self._get_topic_arns()
        self.event_bus_name = os.environ.get('EVENT_BUS_NAME')
    
    def send_alert_notification(self, alert: Dict[str, Any]):
        """Send alert notification to appropriate SNS topic"""
        severity = alert['severity']
        topic_arn = self.topic_arns.get(severity)
        
        if not topic_arn:
            logger.warning(f"No topic ARN found for severity: {severity}")
            return
        
        # Only send notifications for ALARM or INSUFFICIENT_DATA states
        if alert.get('state') in ['ALARM', 'INSUFFICIENT_DATA'] or alert.get('alert_type') == 'custom':
            try:
                message = self._format_alert_message(alert)
                subject = self._format_alert_subject(alert)
                
                self.sns.publish(
                    TopicArn=topic_arn,
                    Message=json.dumps(alert, indent=2),
                    Subject=subject,
                    MessageAttributes={
                        'severity': {
                            'DataType': 'String',
                            'StringValue': severity
                        },
                        'environment': {
                            'DataType': 'String',
                            'StringValue': alert['environment']
                        },
                        'alert_type': {
                            'DataType': 'String',
                            'StringValue': alert['alert_type']
                        }
                    }
                )
                
                logger.info(f"Sent {severity} alert notification")
                
            except ClientError as e:
                logger.error(f"Failed to send SNS notification: {e}")
    
    def send_to_eventbridge(self, alert: Dict[str, Any]):
        """Send alert to EventBridge for automation"""
        if not self.event_bus_name:
            logger.warning("No EventBridge bus configured")
            return
        
        try:
            self.events.put_events(
                Entries=[
                    {
                        'Source': 'observability.alerts',
                        'DetailType': 'Alert Processed',
                        'Detail': json.dumps(alert),
                        'EventBusName': self.event_bus_name
                    }
                ]
            )
            
            logger.info("Sent alert to EventBridge for automation")
            
        except ClientError as e:
            logger.error(f"Failed to send to EventBridge: {e}")
    
    def _get_topic_arns(self) -> Dict[str, str]:
        """Get SNS topic ARNs from environment variables"""
        return {
            'critical': os.environ.get('TOPIC_ARN_CRITICAL') or '',
            'high': os.environ.get('TOPIC_ARN_HIGH') or '',
            'medium': os.environ.get('TOPIC_ARN_MEDIUM') or '',
            'low': os.environ.get('TOPIC_ARN_LOW') or ''
        }
    
    def _format_alert_message(self, alert: Dict[str, Any]) -> str:
        """Format alert message for human readability"""
        if alert['alert_type'] == 'cloudwatch_alarm':
            return f"""
Alert: {alert.get('alarm_name', 'Unknown')}
Severity: {alert['severity'].upper()}
State: {alert.get('state', 'Unknown')}
Time: {alert['timestamp']}
Environment: {alert['environment']}

Reason: {alert.get('reason', 'No reason provided')}

Runbook: {alert.get('runbook_url', 'N/A')}
Dashboard: {alert.get('dashboard_url', 'N/A')}
"""
        else:
            return f"""
Custom Alert: {alert.get('message', 'No message')}
Severity: {alert['severity'].upper()}
Source: {alert.get('source', 'Unknown')}
Time: {alert['timestamp']}
Environment: {alert['environment']}

Runbook: {alert.get('runbook_url', 'N/A')}
"""
    
    def _format_alert_subject(self, alert: Dict[str, Any]) -> str:
        """Format alert subject line"""
        severity = alert['severity'].upper()
        environment = alert['environment'].upper()
        
        if alert['alert_type'] == 'cloudwatch_alarm':
            alarm_name = alert.get('alarm_name', 'Unknown Alarm')
            return f"[{severity}] [{environment}] {alarm_name}"
        else:
            source = alert.get('source', 'Unknown')
            return f"[{severity}] [{environment}] Custom Alert from {source}"