"""
Dashboard management service
"""
import boto3
import json
import logging
from typing import Dict, List

logger = logging.getLogger(__name__)

class DashboardService:
    """Service for managing CloudWatch dashboards"""
    
    def __init__(self):
        self.cloudwatch = boto3.client('cloudwatch')
    
    def update_dashboards(self, resources: Dict[str, List[str]]) -> List[str]:
        """Update dashboards based on discovered resources"""
        updated_dashboards = []
        
        if resources['ec2_instances']:
            self._update_ec2_dashboard(resources['ec2_instances'])
            updated_dashboards.append('EC2')
        
        if resources['lambda_functions']:
            self._update_lambda_dashboard(resources['lambda_functions'])
            updated_dashboards.append('Lambda')
        
        if resources['ecs_clusters']:
            self._update_ecs_dashboard(resources['ecs_clusters'])
            updated_dashboards.append('ECS')
        
        if resources['rds_instances']:
            self._update_rds_dashboard(resources['rds_instances'])
            updated_dashboards.append('RDS')
        
        return updated_dashboards
    
    def _update_ec2_dashboard(self, instances: List[str]):
        """Update EC2 dashboard with current instances"""
        widgets = self._create_ec2_widgets(instances)
        dashboard_body = {
            "widgets": widgets
        }
        
        try:
            self.cloudwatch.put_dashboard(
                DashboardName='Observability-EC2-Auto',
                DashboardBody=json.dumps(dashboard_body)
            )
            logger.info(f"Updated EC2 dashboard with {len(instances)} instances")
        except Exception as e:
            logger.error(f"Failed to update EC2 dashboard: {e}")
    
    def _create_ec2_widgets(self, instances: List[str]) -> List[Dict]:
        """Create EC2 dashboard widgets"""
        widgets = []
        
        # CPU utilization widget
        widgets.append({
            "type": "metric",
            "x": 0, "y": 0,
            "width": 12, "height": 6,
            "properties": {
                "metrics": [
                    ["AWS/EC2", "CPUUtilization", "InstanceId", instance_id]
                    for instance_id in instances[:10]  # Limit to 10 instances
                ],
                "period": 300,
                "stat": "Average",
                "region": "us-east-1",
                "title": "EC2 CPU Utilization"
            }
        })
        
        # Network I/O widget
        widgets.append({
            "type": "metric",
            "x": 12, "y": 0,
            "width": 12, "height": 6,
            "properties": {
                "metrics": [
                    ["AWS/EC2", "NetworkIn", "InstanceId", instance_id]
                    for instance_id in instances[:5]
                ] + [
                    [".", "NetworkOut", ".", instance_id]
                    for instance_id in instances[:5]
                ],
                "period": 300,
                "stat": "Average",
                "region": "us-east-1",
                "title": "EC2 Network I/O"
            }
        })
        
        return widgets
    
    def _update_lambda_dashboard(self, functions: List[str]):
        """Update Lambda dashboard with current functions"""
        widgets = self._create_lambda_widgets(functions)
        dashboard_body = {
            "widgets": widgets
        }
        
        try:
            self.cloudwatch.put_dashboard(
                DashboardName='Observability-Lambda-Auto',
                DashboardBody=json.dumps(dashboard_body)
            )
            logger.info(f"Updated Lambda dashboard with {len(functions)} functions")
        except Exception as e:
            logger.error(f"Failed to update Lambda dashboard: {e}")
    
    def _create_lambda_widgets(self, functions: List[str]) -> List[Dict]:
        """Create Lambda dashboard widgets"""
        widgets = []
        
        # Duration widget
        widgets.append({
            "type": "metric",
            "x": 0, "y": 0,
            "width": 12, "height": 6,
            "properties": {
                "metrics": [
                    ["AWS/Lambda", "Duration", "FunctionName", function_name]
                    for function_name in functions[:10]
                ],
                "period": 300,
                "stat": "Average",
                "region": "us-east-1",
                "title": "Lambda Duration"
            }
        })
        
        # Error rate widget
        widgets.append({
            "type": "metric",
            "x": 12, "y": 0,
            "width": 12, "height": 6,
            "properties": {
                "metrics": [
                    ["AWS/Lambda", "Errors", "FunctionName", function_name]
                    for function_name in functions[:10]
                ],
                "period": 300,
                "stat": "Sum",
                "region": "us-east-1",
                "title": "Lambda Errors"
            }
        })
        
        return widgets
    
    def _update_ecs_dashboard(self, clusters: List[str]):
        """Update ECS dashboard with current clusters"""
        logger.info(f"Would update ECS dashboard with {len(clusters)} clusters")
        # Implementation for ECS dashboard
    
    def _update_rds_dashboard(self, instances: List[str]):
        """Update RDS dashboard with current instances"""
        logger.info(f"Would update RDS dashboard with {len(instances)} instances")
        # Implementation for RDS dashboard