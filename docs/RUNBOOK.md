# Observability Platform Runbook

## Overview
This runbook provides operational procedures for managing the AWS Observability Platform in production environments.

## Emergency Contacts
- **Platform Team**: platform-team@company.com
- **On-Call Engineer**: +1-555-ONCALL
- **AWS Support**: Enterprise Support Case

## Common Operations

### 1. Deployment Issues

#### Symptom: CDK Deploy Fails
```bash
# Check CloudFormation events
aws cloudformation describe-stack-events --stack-name ObservabilityCore-prod

# Check CDK diff
cdk diff --context environment=prod

# Rollback if needed
aws cloudformation cancel-update-stack --stack-name ObservabilityCore-prod
```

#### Symptom: Lambda Function Errors
```bash
# Check function logs
aws logs tail /aws/lambda/observability-alert-processor-prod --follow

# Check function metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Errors \
  --dimensions Name=FunctionName,Value=observability-alert-processor-prod \
  --start-time 2024-01-01T00:00:00Z \
  --end-time 2024-01-01T23:59:59Z \
  --period 300 \
  --statistics Sum
```

### 2. Alert Delivery Issues

#### Symptom: Alerts Not Being Delivered
1. **Check SNS Topic Subscriptions**:
   ```bash
   aws sns list-subscriptions-by-topic --topic-arn arn:aws:sns:region:account:observability-critical-prod
   ```

2. **Verify EventBridge Rules**:
   ```bash
   aws events list-rules --event-bus-name observability-prod
   ```

3. **Check Lambda Processor Logs**:
   ```bash
   aws logs filter-log-events \
     --log-group-name /aws/lambda/observability-alert-processor-prod \
     --filter-pattern "ERROR"
   ```

#### Symptom: Too Many Alerts
1. **Temporarily Disable Non-Critical Alarms**:
   ```bash
   aws cloudwatch disable-alarm-actions --alarm-names \
     "observability-medium-cpu-prod" \
     "observability-low-disk-space-prod"
   ```

2. **Adjust Thresholds**:
   - Update configuration in `src/config/environment_config.py`
   - Redeploy with `cdk deploy`

### 3. Cost Overruns

#### Symptom: Budget Alert Triggered
1. **Identify Top Cost Drivers**:
   ```bash
   aws ce get-cost-and-usage \
     --time-period Start=2024-01-01,End=2024-01-31 \
     --granularity MONTHLY \
     --metrics BlendedCost \
     --group-by Type=DIMENSION,Key=SERVICE
   ```

2. **Check CloudWatch Costs**:
   - Review metric ingestion rates
   - Check log retention policies
   - Verify dashboard usage

3. **Immediate Cost Reduction**:
   ```bash
   # Reduce log retention temporarily
   aws logs put-retention-policy \
     --log-group-name /observability/platform \
     --retention-in-days 7
   ```

### 4. Performance Issues

#### Symptom: Dashboard Loading Slowly
1. **Check CloudWatch API Throttling**:
   ```bash
   aws logs filter-log-events \
     --log-group-name /aws/lambda/observability-dashboard-updater-prod \
     --filter-pattern "Throttling"
   ```

2. **Optimize Dashboard Queries**:
   - Reduce time range for widgets
   - Decrease refresh frequency
   - Use metric math for complex calculations

#### Symptom: Log Processing Delays
1. **Check Kinesis Stream Metrics**:
   ```bash
   aws cloudwatch get-metric-statistics \
     --namespace AWS/Kinesis \
     --metric-name IncomingRecords \
     --dimensions Name=StreamName,Value=observability-logs-prod
   ```

2. **Scale Processing Lambda**:
   ```bash
   aws lambda put-provisioned-concurrency-config \
     --function-name observability-log-processor-prod \
     --provisioned-concurrency-config ProvisionedConcurrencyConfig=100
   ```

## Monitoring the Monitor

### Key Metrics to Watch
- **Lambda Error Rates**: Should be < 1%
- **SNS Delivery Failures**: Should be 0
- **EventBridge Failed Invocations**: Should be < 0.1%
- **CloudWatch API Throttling**: Should be minimal
- **Cost Trends**: Monitor for unexpected spikes

### Health Check Commands
```bash
# Platform health check
python scripts/health_check.py --environment prod

# Verify all stacks are healthy
aws cloudformation list-stacks --stack-status-filter CREATE_COMPLETE UPDATE_COMPLETE

# Check recent deployments
aws cloudformation describe-stack-events --stack-name ObservabilityCore-prod --max-items 10
```

## Recovery Procedures

### Complete Platform Failure
1. **Assess Scope**: Determine which stacks are affected
2. **Communicate**: Notify stakeholders via backup channels
3. **Rollback**: Use CloudFormation rollback capabilities
4. **Restore**: Deploy from known good configuration
5. **Validate**: Run health checks and verify functionality

### Data Loss Scenarios
1. **CloudWatch Logs**: Check S3 backup bucket
2. **Metrics**: Historical data may be lost, focus on restoring collection
3. **Dashboards**: Redeploy from CDK configuration

## Escalation Procedures

### Level 1: Platform Team
- Initial response and basic troubleshooting
- Access to logs and basic AWS console operations

### Level 2: Senior Engineers
- Complex troubleshooting and configuration changes
- Authority to modify thresholds and disable alarms

### Level 3: AWS Support
- Infrastructure-level issues
- Service limit increases
- AWS service outages

## Maintenance Windows

### Monthly Tasks
- Review and update alert thresholds
- Clean up old log groups and unused resources
- Update CDK and dependency versions
- Review cost optimization opportunities

### Quarterly Tasks
- Security review and access audit
- Performance optimization review
- Disaster recovery testing
- Documentation updates

## Contact Information

| Role | Contact | Availability |
|------|---------|--------------|
| Platform Lead | platform-lead@company.com | Business hours |
| On-Call Engineer | oncall@company.com | 24/7 |
| AWS TAM | tam@amazon.com | Business hours |
| Security Team | security@company.com | Business hours |