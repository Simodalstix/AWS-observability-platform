# AWS Observability Platform

[![CI](https://github.com/username/AWS-observability-platform/actions/workflows/ci.yml/badge.svg)](https://github.com/username/AWS-observability-platform/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/username/AWS-observability-platform/branch/main/graph/badge.svg)](https://codecov.io/gh/username/AWS-observability-platform)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Release](https://img.shields.io/github/v/release/username/AWS-observability-platform)](https://github.com/username/AWS-observability-platform/releases)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)

A comprehensive, enterprise-ready monitoring and observability platform built with AWS CDK that provides instant visibility into any AWS workload with minimal configuration.

## Problem Statement

Modern cloud applications generate massive amounts of telemetry data across multiple AWS services, making it challenging to:
- **Gain unified visibility** across distributed systems
- **Detect and respond** to incidents before they impact users
- **Optimize costs** while maintaining performance and reliability
- **Scale monitoring** as infrastructure grows

This platform solves these challenges by providing automated, intelligent observability that scales with your infrastructure.

## Features

### Core Monitoring
- **Universal Resource Discovery**: Automatically detects and monitors EC2, ECS, EKS, Lambda, RDS, and more
- **Custom Metrics Collection**: Application-level metrics with automated collection
- **Distributed Tracing**: X-Ray integration for service maps and performance analysis
- **Real-time Dashboards**: Pre-built CloudWatch dashboards with business metrics

### Intelligent Alerting
- **Multi-severity Alerts**: Critical, High, Medium, Low with appropriate routing
- **Multi-channel Notifications**: SNS, email, Slack integration ready
- **Composite Alarms**: System-wide health indicators
- **Alert Enrichment**: Automatic runbook and dashboard links

### Automation & Remediation
- **EventBridge-driven Workflows**: Automated response to incidents
- **Step Functions Integration**: Complex remediation workflows
- **Auto-scaling Logic**: Intelligent resource scaling based on metrics
- **Incident Response**: Automated escalation and notification

### Cost Optimization
- **Budget Monitoring**: Automated budget alerts and forecasting
- **Anomaly Detection**: Cost spike detection with root cause analysis
- **Optimization Recommendations**: Automated cost-saving suggestions
- **Resource Rightsizing**: Underutilized resource identification

### Log Intelligence
- **Automated Log Processing**: Structured log parsing and enrichment
- **Anomaly Detection**: Pattern recognition for unusual log behavior
- **Scheduled Insights**: Pre-configured CloudWatch Logs Insights queries
- **Real-time Analysis**: Kinesis-based log streaming and processing

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Applications  │    │   AWS Services  │    │  Custom Metrics │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          └──────────────────────┼──────────────────────┘
                                 │
                    ┌─────────────▼─────────────┐
                    │    Observability Core     │
                    │  ┌─────────────────────┐  │
                    │  │   EventBridge Bus   │  │
                    │  └─────────────────────┘  │
                    └─────────────┬─────────────┘
                                  │
        ┌─────────────────────────┼─────────────────────────┐
        │                         │                         │
┌───────▼────────┐    ┌──────────▼──────────┐    ┌─────────▼────────┐
│   Dashboards   │    │      Alerting       │    │    Automation    │
│                │    │                     │    │                  │
│ • Overview     │    │ • Multi-channel     │    │ • Remediation    │
│ • Service      │    │ • Severity-based    │    │ • Auto-scaling   │
│ • Cost         │    │ • Enriched alerts   │    │ • Workflows      │
└────────────────┘    └─────────────────────┘    └──────────────────┘
        │                         │                         │
        └─────────────────────────┼─────────────────────────┘
                                  │
                    ┌─────────────▼─────────────┐
                    │      Log Analysis        │
                    │                          │
                    │ • Stream Processing      │
                    │ • Anomaly Detection      │
                    │ • Insights Queries       │
                    └──────────────────────────┘
```

## Quick Start

### Prerequisites
- AWS CLI configured with appropriate permissions
- AWS CDK v2 installed (`npm install -g aws-cdk`)
- Python 3.9+ with pip

### Installation

1. **Clone and setup:**
   ```bash
   git clone <repository-url>
   cd AWS-observability-platform
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Deploy the platform:**
   ```bash
   python deploy.py
   ```

3. **Follow the prompts:**
   - Select environment (dev/staging/prod)
   - Confirm AWS account and region
   - Wait for deployment to complete

### Manual Deployment

```bash
# Install dependencies
pip install -r requirements.txt

# Bootstrap CDK (first time only)
cdk bootstrap

# Deploy all stacks
cdk deploy --all --context environment=dev
```

## Stack Components

### Core Stack (`CoreObservabilityStack`)
- KMS encryption for all observability data
- S3 bucket for long-term storage with lifecycle policies
- CloudWatch log groups with appropriate retention
- IAM roles with least-privilege permissions
- Custom EventBridge bus for platform events
- X-Ray configuration with sampling rules

### Dashboard Stack (`DashboardStack`)
- **Overview Dashboard**: System-wide health and metrics
- **Service Dashboards**: EC2, Lambda, RDS, ECS specific views
- **Auto-discovery**: Dynamically updates based on discovered resources
- **Log Insights Widgets**: Pre-configured queries for common scenarios

### Alerting Stack (`AlertingStack`)
- **Multi-severity Topics**: Critical, High, Medium, Low SNS topics
- **Alert Processing**: Lambda function for enrichment and routing
- **Default Alarms**: Common scenarios (high CPU, Lambda errors, etc.)
- **Composite Alarms**: System health indicators

### Automation Stack (`AutomationStack`)
- **Remediation Functions**: EC2 restart, Lambda restart, ECS scaling
- **Step Functions Workflows**: Complex multi-step remediation
- **Auto-scaling Logic**: Intelligent resource scaling
- **Incident Response**: Automated escalation workflows

### Cost Monitoring Stack (`CostMonitoringStack`)
- **Budget Alerts**: Monthly and service-specific budgets
- **Anomaly Detection**: Cost spike identification
- **Optimization Engine**: Underutilized resource detection
- **Cost Dashboard**: Trend analysis and forecasting

### Log Analysis Stack (`LogAnalysisStack`)
- **Kinesis Streaming**: Real-time log processing
- **Log Enrichment**: Structured parsing and metadata addition
- **Scheduled Queries**: Automated CloudWatch Logs Insights
- **Anomaly Detection**: Pattern recognition for unusual behavior

## Configuration

### Environment-specific Settings

Create context files for different environments:

```json
// cdk.context.json
{
  "dev": {
    "budget_limit": 100,
    "log_retention_days": 30,
    "alert_email": "dev-team@company.com"
  },
  "prod": {
    "budget_limit": 1000,
    "log_retention_days": 180,
    "alert_email": "ops-team@company.com"
  }
}
```

### Custom Metrics

Add application-specific metrics:

```python
# In your application code
import boto3

cloudwatch = boto3.client('cloudwatch')
cloudwatch.put_metric_data(
    Namespace='MyApp/Business',
    MetricData=[
        {
            'MetricName': 'OrdersProcessed',
            'Value': 1,
            'Dimensions': [
                {'Name': 'Environment', 'Value': 'prod'},
                {'Name': 'Service', 'Value': 'order-service'}
            ]
        }
    ]
)
```

## Monitoring Integration

### For Existing Applications

1. **Add structured logging:**
   ```python
   import json
   import logging
   
   logger = logging.getLogger()
   
   def handler(event, context):
       logger.info(json.dumps({
           'event_type': 'request_processed',
           'user_id': event.get('user_id'),
           'duration_ms': 150,
           'status': 'success'
       }))
   ```

2. **Enable X-Ray tracing:**
   ```python
   from aws_xray_sdk.core import xray_recorder
   
   @xray_recorder.capture('business_logic')
   def process_order(order_data):
       # Your business logic
       pass
   ```

3. **Send custom alerts:**
   ```python
   import boto3
   
   events = boto3.client('events')
   events.put_events(
       Entries=[{
           'Source': 'myapp.business',
           'DetailType': 'Business Alert',
           'Detail': json.dumps({
               'severity': 'high',
               'message': 'Payment processing failed',
               'order_id': '12345'
           }),
           'EventBusName': 'observability-prod'
       }]
   )
   ```

## Troubleshooting

### Common Issues

1. **Deployment Failures**
   - Check AWS credentials and permissions
   - Verify CDK bootstrap in target region
   - Review CloudFormation events in AWS Console

2. **Missing Metrics**
   - Verify IAM permissions for CloudWatch
   - Check metric namespace and dimensions
   - Review Lambda function logs

3. **Alert Delivery Issues**
   - Confirm SNS topic subscriptions
   - Check email spam folders
   - Verify EventBridge rule patterns

### Debug Commands

```bash
# Check stack status
cdk list
cdk diff

# View logs
aws logs tail /observability/platform --follow

# Test EventBridge rules
aws events put-events --entries file://test-event.json
```

## Security

- All data encrypted at rest using KMS
- Least-privilege IAM roles and policies
- VPC endpoints for private communication (optional)
- CloudTrail integration for audit logging
- Secrets Manager for sensitive configuration

## Cost Optimization

The platform includes built-in cost optimization:

- **Lifecycle Policies**: Automatic data archival to reduce storage costs
- **Sampling Rules**: X-Ray sampling to control tracing costs
- **Log Retention**: Configurable retention periods
- **Resource Tagging**: Automatic cost allocation tags
- **Budget Alerts**: Proactive cost monitoring

Estimated monthly costs:
- **Dev Environment**: $20-50
- **Production Environment**: $100-300 (depending on scale)

## Testing

### Running Tests

```bash
# Install test dependencies
pip install -r requirements-dev.txt

# Run unit tests
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ --cov=src --cov-report=html

# Run CDK tests
cdk synth --all
```

### Test Structure

- `tests/test_config_manager.py` - Configuration validation tests
- `tests/test_metric_calculator.py` - Metric calculation logic tests
- Integration tests validate CDK synthesis and deployment

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for new functionality
5. Run the test suite (`python -m pytest`)
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

- **Documentation**: Check the `docs/` directory for detailed guides
- **Issues**: Report bugs and feature requests via GitHub Issues
- **Discussions**: Join the community discussions for questions and ideas

## Roadmap

- [ ] Grafana integration for advanced visualization
- [ ] Prometheus metrics export
- [ ] Multi-region deployment support
- [ ] Advanced ML-based anomaly detection
- [ ] Integration with AWS Security Hub
- [ ] Custom notification channels (Teams, PagerDuty)
- [ ] Infrastructure as Code scanning
- [ ] Compliance reporting automation

## Why This Matters

This project demonstrates real-world cloud engineering expertise:

- **Infrastructure as Code**: Complete AWS CDK implementation with proper abstractions
- **Observability Engineering**: Production-ready monitoring, alerting, and automation
- **Cost Optimization**: Built-in budget monitoring and resource optimization
- **Security Best Practices**: KMS encryption, least-privilege IAM, and audit logging
- **Operational Excellence**: Automated remediation, incident response, and runbooks
- **Scalable Architecture**: Event-driven design that grows with your infrastructure

Built for enterprise environments where reliability, security, and cost efficiency are critical.