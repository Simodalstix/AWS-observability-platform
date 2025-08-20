"""
EC2 remediation Lambda function
"""
import boto3
import json
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

ec2 = boto3.client('ec2')
cloudwatch = boto3.client('cloudwatch')

def handler(event, context):
    """Handle EC2 remediation actions"""
    try:
        action = event.get('action', 'restart')
        
        if action == 'restart':
            return restart_instance(event, context)
        elif action == 'check_health':
            return check_instance_health(event, context)
        elif action == 'verify':
            return verify_instance_recovery(event, context)
        else:
            return {'status': 'error', 'error': f'Unknown action: {action}'}
            
    except Exception as e:
        logger.error(f"Error in EC2 remediation: {str(e)}")
        return {'status': 'error', 'error': str(e)}

def restart_instance(event, context):
    """Restart EC2 instance"""
    instance_id = event.get('instance_id') or event.get('resource_id')
    if not instance_id:
        return {'status': 'error', 'error': 'No instance_id provided'}
    
    try:
        # Check instance state
        response = ec2.describe_instances(InstanceIds=[instance_id])
        instance = response['Reservations'][0]['Instances'][0]
        
        if instance['State']['Name'] != 'running':
            return {'status': 'skipped', 'reason': 'instance_not_running'}
        
        # Restart instance
        ec2.reboot_instances(InstanceIds=[instance_id])
        
        # Send metric
        cloudwatch.put_metric_data(
            Namespace='Observability/Automation',
            MetricData=[{
                'MetricName': 'InstanceRestart',
                'Value': 1,
                'Dimensions': [{'Name': 'InstanceId', 'Value': instance_id}]
            }]
        )
        
        return {'status': 'success', 'instance_id': instance_id}
        
    except Exception as e:
        logger.error(f"Error restarting instance {instance_id}: {str(e)}")
        return {'status': 'error', 'error': str(e)}

def check_instance_health(event, context):
    """Check instance health"""
    instance_id = event.get('instance_id') or event.get('resource_id')
    if not instance_id:
        return {'status': 'error', 'error': 'No instance_id provided'}
    
    try:
        response = ec2.describe_instances(InstanceIds=[instance_id])
        instance = response['Reservations'][0]['Instances'][0]
        state = instance['State']['Name']
        
        return {
            'status': 'healthy' if state == 'running' else 'unhealthy',
            'instance_state': state,
            'instance_id': instance_id
        }
        
    except Exception as e:
        return {'status': 'error', 'error': str(e)}

def verify_instance_recovery(event, context):
    """Verify instance has recovered"""
    return check_instance_health(event, context)