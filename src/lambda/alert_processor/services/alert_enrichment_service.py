"""
Alert enrichment service
Adds context and metadata to alerts
"""
import os
import logging
from datetime import datetime, timezone
from typing import Dict, Any

logger = logging.getLogger(__name__)

class AlertEnrichmentService:
    """Service for enriching alerts with additional context"""
    
    def __init__(self):
        self.environment = os.environ.get('ENVIRONMENT', 'unknown')
        self.runbook_base_url = os.environ.get('RUNBOOK_BASE_URL', 'https://runbooks.example.com')
    
    def enrich_cloudwatch_alarm(self, alarm_detail: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich CloudWatch alarm with additional context"""
        alarm_name = alarm_detail['alarmName']
        state = alarm_detail['state']['value']
        reason = alarm_detail['state']['reason']
        
        enriched_alert = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'alert_type': 'cloudwatch_alarm',
            'alarm_name': alarm_name,
            'state': state,
            'reason': reason,
            'severity': self._determine_severity(alarm_name, alarm_detail),
            'environment': self.environment,
            'runbook_url': self._generate_runbook_url(alarm_name),
            'dashboard_url': self._generate_dashboard_url(alarm_name),
            'source_detail': alarm_detail
        }
        
        return enriched_alert
    
    def enrich_custom_alert(self, alert_detail: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich custom application alert"""
        severity = alert_detail.get('severity', 'medium')
        message = alert_detail.get('message', '')
        source = alert_detail.get('source', 'unknown')
        
        enriched_alert = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'alert_type': 'custom',
            'severity': severity,
            'message': message,
            'source': source,
            'environment': self.environment,
            'runbook_url': self._generate_runbook_url(f"custom-{source}"),
            'source_detail': alert_detail
        }
        
        return enriched_alert
    
    def _determine_severity(self, alarm_name: str, detail: Dict[str, Any]) -> str:
        """Determine alert severity based on alarm characteristics"""
        alarm_name_lower = alarm_name.lower()
        
        # Critical severity indicators
        if any(keyword in alarm_name_lower for keyword in ['critical', 'fatal', 'down', 'outage']):
            return 'critical'
        
        # High severity indicators
        if any(keyword in alarm_name_lower for keyword in ['error', 'high', 'failed', 'timeout']):
            return 'high'
        
        # Medium severity indicators
        if any(keyword in alarm_name_lower for keyword in ['warning', 'medium', 'slow']):
            return 'medium'
        
        # Default to low
        return 'low'
    
    def _generate_runbook_url(self, identifier: str) -> str:
        """Generate runbook URL based on alert identifier"""
        sanitized_id = identifier.lower().replace(' ', '-').replace('_', '-')
        return f"{self.runbook_base_url}/{sanitized_id}"
    
    def _generate_dashboard_url(self, alarm_name: str) -> str:
        """Generate CloudWatch dashboard URL"""
        region = os.environ.get('AWS_REGION', 'us-east-1')
        return f"https://console.aws.amazon.com/cloudwatch/home?region={region}#dashboards:"