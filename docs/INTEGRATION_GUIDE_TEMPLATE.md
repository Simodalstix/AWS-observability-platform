# AWS Observability Platform Integration Guide

## Quick Start

### Lambda Functions
```python
import boto3
import json
from aws_xray_sdk.core import xray_recorder

cloudwatch = boto3.client('cloudwatch')

@xray_recorder.capture('business_logic')
def lambda_handler(event, context):
    # Send custom metrics
    cloudwatch.put_metric_data(
        Namespace='MyApp/Lambda',
        MetricData=[{
            'MetricName': 'RequestsProcessed',
            'Value': 1
        }]
    )
    
    # Structured logging
    print(json.dumps({
        'event_type': 'request_processed',
        'request_id': context.aws_request_id
    }))
```

### Custom Alerts
```python
import boto3

events = boto3.client('events')
events.put_events(
    Entries=[{
        'Source': 'myapp.alerts',
        'DetailType': 'Custom Alert',
        'Detail': json.dumps({
            'severity': 'high',
            'message': 'Business logic alert'
        }),
        'EventBusName': 'observability-{environment}'
    }]
)
```

## Environment Variables
- `OBSERVABILITY_EVENT_BUS`: Custom EventBridge bus name
- `OBSERVABILITY_ENVIRONMENT`: Environment name (dev/staging/prod)

## Dashboard URLs
- Overview: https://console.aws.amazon.com/cloudwatch/home#dashboards:name=Observability-Overview-{env}
- Service-specific: https://console.aws.amazon.com/cloudwatch/home#dashboards:name=Observability-{SERVICE}-{env}

## Troubleshooting
1. Check CloudWatch Logs: `/observability/platform`
2. Review EventBridge events for automation status
3. Check SNS topics for alert delivery