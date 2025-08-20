"""
Dashboard updater Lambda function
Discovers AWS resources and updates CloudWatch dashboards
"""
import json
import logging
from typing import Dict, List
from .services.resource_discovery import ResourceDiscoveryService
from .services.dashboard_service import DashboardService

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def handler(event, context):
    """Main Lambda handler for dashboard updates"""
    try:
        # Initialize services
        discovery_service = ResourceDiscoveryService()
        dashboard_service = DashboardService()
        
        # Discover resources
        resources = discovery_service.discover_all_resources()
        logger.info(f"Discovered {sum(len(v) for v in resources.values())} resources")
        
        # Update dashboards
        updated_dashboards = dashboard_service.update_dashboards(resources)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Dashboards updated successfully',
                'resources_discovered': resources,
                'dashboards_updated': updated_dashboards
            })
        }
        
    except Exception as e:
        logger.error(f"Error updating dashboards: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }