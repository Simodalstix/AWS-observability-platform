"""
Alert processor Lambda function
Processes and enriches CloudWatch alarms and custom alerts
"""
import json
import logging
from .services.alert_enrichment_service import AlertEnrichmentService
from .services.notification_service import NotificationService

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def handler(event, context):
    """Main Lambda handler for alert processing"""
    try:
        # Initialize services
        enrichment_service = AlertEnrichmentService()
        notification_service = NotificationService()
        
        # Process different types of events
        if _is_cloudwatch_alarm(event):
            return _process_cloudwatch_alarm(event, enrichment_service, notification_service)
        elif _is_custom_alert(event):
            return _process_custom_alert(event, enrichment_service, notification_service)
        else:
            logger.warning(f"Unknown event type: {event}")
            return {'statusCode': 400, 'body': 'Unknown event type'}
        
    except Exception as e:
        logger.error(f"Error processing alert: {str(e)}", exc_info=True)
        return {'statusCode': 500, 'body': json.dumps({'error': str(e)})}

def _is_cloudwatch_alarm(event) -> bool:
    """Check if event is a CloudWatch alarm"""
    return event.get('source') == 'aws.cloudwatch'

def _is_custom_alert(event) -> bool:
    """Check if event is a custom alert"""
    return 'Custom' in event.get('detail-type', '')

def _process_cloudwatch_alarm(event, enrichment_service, notification_service):
    """Process CloudWatch alarm state change"""
    detail = event['detail']
    
    # Enrich the alert
    enriched_alert = enrichment_service.enrich_cloudwatch_alarm(detail)
    
    # Send notifications
    notification_service.send_alert_notification(enriched_alert)
    
    # Forward to EventBridge for automation
    notification_service.send_to_eventbridge(enriched_alert)
    
    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': 'CloudWatch alarm processed',
            'alarm_name': detail['alarmName'],
            'severity': enriched_alert['severity']
        })
    }

def _process_custom_alert(event, enrichment_service, notification_service):
    """Process custom application alert"""
    detail = event['detail']
    
    # Enrich the alert
    enriched_alert = enrichment_service.enrich_custom_alert(detail)
    
    # Send notifications
    notification_service.send_alert_notification(enriched_alert)
    
    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': 'Custom alert processed',
            'severity': enriched_alert['severity']
        })
    }