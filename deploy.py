#!/usr/bin/env python3
"""
Deployment script for AWS Observability Platform
"""
import subprocess
import sys
import json
import boto3
from typing import Dict, Any

def check_prerequisites():
    """Check if required tools are installed"""
    required_tools = ['aws', 'cdk']
    
    for tool in required_tools:
        try:
            subprocess.run([tool, '--version'], check=True, capture_output=True)
            print(f"✓ {tool} is installed")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print(f"✗ {tool} is not installed or not in PATH")
            return False
    
    return True

def get_aws_account_info():
    """Get AWS account and region information"""
    try:
        sts = boto3.client('sts')
        identity = sts.get_caller_identity()
        
        session = boto3.Session()
        region = session.region_name or 'us-east-1'
        
        return {
            'account': identity['Account'],
            'region': region
        }
    except Exception as e:
        print(f"Error getting AWS account info: {e}")
        return None

def bootstrap_cdk(account: str, region: str):
    """Bootstrap CDK in the target account/region"""
    print(f"Bootstrapping CDK in account {account}, region {region}...")
    
    try:
        subprocess.run([
            'cdk', 'bootstrap', 
            f'aws://{account}/{region}'
        ], check=True)
        print("✓ CDK bootstrap completed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ CDK bootstrap failed: {e}")
        return False

def install_dependencies():
    """Install Python dependencies"""
    print("Installing Python dependencies...")
    
    try:
        subprocess.run([
            sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'
        ], check=True)
        print("✓ Dependencies installed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to install dependencies: {e}")
        return False

def deploy_stacks(environment: str, account: str, region: str):
    """Deploy CDK stacks"""
    print(f"Deploying observability platform for environment: {environment}")
    
    # Set context variables
    context_args = [
        '--context', f'environment={environment}',
        '--context', f'account={account}',
        '--context', f'region={region}'
    ]
    
    try:
        # Deploy all stacks
        subprocess.run([
            'cdk', 'deploy', '--all', '--require-approval', 'never'
        ] + context_args, check=True)
        
        print("✓ All stacks deployed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Deployment failed: {e}")
        return False

def create_integration_guide():
    """Create integration guide for existing projects"""
    guide_content = """
# AWS Observability Platform Integration Guide

## Quick Start

1. **Add monitoring to existing Lambda functions:**
   ```python
   import boto3
   
   # Send custom metrics
   cloudwatch = boto3.client('cloudwatch')
   cloudwatch.put_metric_data(
       Namespace='MyApp/Lambda',
       MetricData=[
           {
               'MetricName': 'BusinessMetric',
               'Value': 1,
               'Dimensions': [
                   {'Name': 'FunctionName', 'Value': 'my-function'}
               ]
           }
       ]
   )
   ```

2. **Add structured logging:**
   ```python
   import json
   import logging
   
   logger = logging.getLogger()
   logger.setLevel(logging.INFO)
   
   def lambda_handler(event, context):
       logger.info(json.dumps({
           'event_type': 'request_received',
           'request_id': context.aws_request_id,
           'user_id': event.get('user_id'),
           'timestamp': datetime.utcnow().isoformat()
       }))
   ```

3. **Enable X-Ray tracing:**
   ```python
   from aws_xray_sdk.core import xray_recorder
   from aws_xray_sdk.core import patch_all
   
   # Patch AWS SDK calls
   patch_all()
   
   @xray_recorder.capture('my_function')
   def my_function():
       # Your code here
       pass
   ```

## Environment Variables

Set these environment variables in your applications:

- `OBSERVABILITY_EVENT_BUS`: Custom EventBridge bus name
- `OBSERVABILITY_ENVIRONMENT`: Environment name (dev/staging/prod)

## Custom Alerts

Send custom alerts to the platform:

```python
import boto3

events = boto3.client('events')
events.put_events(
    Entries=[
        {
            'Source': 'myapp.alerts',
            'DetailType': 'Custom Alert',
            'Detail': json.dumps({
                'severity': 'high',
                'message': 'Custom business logic alert',
                'source': 'my-application'
            }),
            'EventBusName': 'observability-{environment}'
        }
    ]
)
```

## Dashboard Integration

Access your dashboards:
- Overview: https://console.aws.amazon.com/cloudwatch/home#dashboards:name=Observability-Overview-{env}
- Service-specific: https://console.aws.amazon.com/cloudwatch/home#dashboards:name=Observability-{SERVICE}-{env}
- Cost: https://console.aws.amazon.com/cloudwatch/home#dashboards:name=Observability-Cost-{env}

## Runbooks

Common troubleshooting scenarios:

### High Lambda Error Rate
1. Check CloudWatch Logs for error details
2. Review X-Ray traces for performance issues
3. Check recent deployments
4. Verify environment variables and permissions

### High EC2 CPU Usage
1. Check CloudWatch metrics for the specific instance
2. Review application logs
3. Consider auto-scaling if appropriate
4. Check for resource-intensive processes

### Cost Anomalies
1. Review Cost Explorer for detailed breakdown
2. Check for new resources or increased usage
3. Review optimization recommendations
4. Consider rightsizing resources

## Support

For issues or questions:
1. Check CloudWatch Logs: `/observability/platform`
2. Review EventBridge events for automation status
3. Check SNS topics for alert delivery
"""
    
    with open('INTEGRATION_GUIDE.md', 'w') as f:
        f.write(guide_content)
    
    print("✓ Integration guide created: INTEGRATION_GUIDE.md")

def main():
    """Main deployment function"""
    print("🚀 AWS Observability Platform Deployment")
    print("=" * 50)
    
    # Check prerequisites
    if not check_prerequisites():
        print("Please install missing prerequisites and try again.")
        sys.exit(1)
    
    # Get AWS account info
    aws_info = get_aws_account_info()
    if not aws_info:
        print("Could not get AWS account information. Please check your AWS credentials.")
        sys.exit(1)
    
    print(f"Deploying to account: {aws_info['account']}")
    print(f"Region: {aws_info['region']}")
    
    # Get environment
    environment = input("Enter environment (dev/staging/prod) [dev]: ").strip() or "dev"
    
    # Install dependencies
    if not install_dependencies():
        sys.exit(1)
    
    # Bootstrap CDK
    if not bootstrap_cdk(aws_info['account'], aws_info['region']):
        sys.exit(1)
    
    # Deploy stacks
    if not deploy_stacks(environment, aws_info['account'], aws_info['region']):
        sys.exit(1)
    
    # Create integration guide
    create_integration_guide()
    
    print("\n🎉 Deployment completed successfully!")
    print("\nNext steps:")
    print("1. Review the INTEGRATION_GUIDE.md file")
    print("2. Configure email addresses for alerts in SNS topics")
    print("3. Set up Slack integration if needed")
    print("4. Review and customize dashboards")
    print("5. Test the monitoring with sample applications")

if __name__ == "__main__":
    main()