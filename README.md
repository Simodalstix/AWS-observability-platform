# AWS Observability Platform

[![CI](https://github.com/username/AWS-observability-platform/actions/workflows/ci.yml/badge.svg)](https://github.com/username/AWS-observability-platform/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Release](https://img.shields.io/github/v/release/username/AWS-observability-platform)](https://github.com/username/AWS-observability-platform/releases)

A production-ready AWS monitoring platform built with CDK. Automatically monitors your AWS resources with dashboards, alerts, and cost tracking.

**What it does**: Deploys comprehensive monitoring for EC2, Lambda, RDS, and other AWS services with zero configuration.

## Features

- **Automated Monitoring**: Discovers and monitors EC2, Lambda, RDS, ECS automatically
- **Smart Alerting**: Multi-level alerts (Critical/High/Medium/Low) with SNS integration
- **Cost Tracking**: Budget alerts and cost anomaly detection
- **Dashboards**: Pre-built CloudWatch dashboards for all services
- **Auto-Remediation**: Step Functions workflows for common issues
- **Log Analysis**: CloudWatch Logs Insights with scheduled queries

## Architecture

```
AWS Services → CloudWatch/X-Ray → EventBridge → [Dashboards + Alerts + Automation]
                                                        ↓
                                               SNS Topics → Email/Slack
                                                        ↓
                                               Step Functions → Auto-remediation
```

**6 CDK Stacks**:
- Core: KMS, S3, EventBridge, IAM roles
- Dashboards: CloudWatch dashboards for all services
- Alerting: Multi-severity SNS topics and alarms
- Automation: Step Functions for remediation
- Cost Monitoring: Budget alerts and anomaly detection
- Log Analysis: CloudWatch Logs Insights automation

## Quick Start

**Prerequisites**: AWS CLI configured, CDK v2 installed, Python 3.9+

```bash
# Clone and setup
git clone <repository-url>
cd AWS-observability-platform
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Deploy (first time)
cdk bootstrap
cdk deploy --all --context environment=dev

# Or use the deployment script
python deploy.py
```

**Result**: Complete monitoring setup for your AWS account in ~10 minutes.

## What Gets Deployed

- **6 CloudFormation stacks** with 50+ AWS resources
- **Pre-configured dashboards** for EC2, Lambda, RDS, ECS
- **4-tier alerting** (Critical → High → Medium → Low)
- **Cost monitoring** with budget alerts
- **Auto-remediation** workflows for common issues
- **Log analysis** with scheduled insights queries

**Estimated cost**: $20-50/month for dev, $100-300/month for production

## Configuration

Environment settings in `src/config/environment_config.py`:

```python
# Customize thresholds, budgets, retention periods
DEV_CONFIG = {
    "budget_limit": 100,
    "cpu_threshold": 85,
    "log_retention_days": 30
}
```

## Integration

**Automatic**: Monitors existing AWS resources immediately after deployment.

**Custom metrics**: Send to CloudWatch with namespace `MyApp/*`

**Custom alerts**: Send events to the EventBridge bus for automation

## Troubleshooting

**Deployment fails**: Check AWS credentials and CDK bootstrap

**No alerts**: Verify SNS topic email subscriptions in AWS Console

**Debug**: Use `cdk diff` and check CloudFormation events

## Security & Cost

**Security**: KMS encryption, least-privilege IAM, no hardcoded secrets

**Cost Control**: Configurable log retention, budget alerts, lifecycle policies

## Testing

```bash
# Run tests
python -m pytest tests/

# Test CDK synthesis
cdk synth --all
```

## Contributing

1. Fork and create feature branch
2. Make changes and test with `cdk synth`
3. Submit pull request

## License

MIT License - see LICENSE file

## Why This Matters

Demonstrates practical AWS skills:
- **CDK Infrastructure as Code**: 6 stacks, 50+ resources, proper abstractions
- **Production Monitoring**: Real alerting, dashboards, cost tracking
- **Automation**: Step Functions workflows for incident response
- **AWS Best Practices**: KMS encryption, least-privilege IAM, proper tagging

Built for real production use, not just a demo.