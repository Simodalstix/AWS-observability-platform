from aws_cdk import (
    Stack,
    aws_budgets as budgets,
    aws_lambda as lambda_,
    aws_events as events,
    aws_events_targets as targets,
    aws_cloudwatch as cloudwatch,
    Duration
)
from constructs import Construct
from typing import Dict, Any, List

class CostMonitoringStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, environment: str, core_resources: Dict[str, Any], **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        self.env_name = environment
        self.core_resources = core_resources
        self.cost_resources = {}
        
        # Create cost monitoring components
        self._create_budgets()
        self._create_cost_anomaly_detector()
        self._create_cost_optimizer()
        self._create_cost_dashboard()
    
    def _create_budgets(self):
        """Create AWS Budgets for cost monitoring"""
        
        # Monthly budget
        monthly_budget = budgets.CfnBudget(
            self, "MonthlyBudget",
            budget=budgets.CfnBudget.BudgetDataProperty(
                budget_name=f"observability-monthly-budget-{self.env_name}",
                budget_type="COST",
                time_unit="MONTHLY",
                budget_limit=budgets.CfnBudget.SpendProperty(
                    amount=1000 if self.env_name == "prod" else 100,  # $1000 for prod, $100 for dev
                    unit="USD"
                ),
                cost_filters=budgets.CfnBudget.CostFiltersProperty(
                    tag_key=["Environment"],
                    tag_value=[self.env_name]
                )
            ),
            notifications_with_subscribers=[
                budgets.CfnBudget.NotificationWithSubscribersProperty(
                    notification=budgets.CfnBudget.NotificationProperty(
                        notification_type="ACTUAL",
                        comparison_operator="GREATER_THAN",
                        threshold=80,
                        threshold_type="PERCENTAGE"
                    ),
                    subscribers=[
                        budgets.CfnBudget.SubscriberProperty(
                            subscription_type="EMAIL",
                            address="admin@example.com"  # Replace with actual email
                        )
                    ]
                ),
                budgets.CfnBudget.NotificationWithSubscribersProperty(
                    notification=budgets.CfnBudget.NotificationProperty(
                        notification_type="FORECASTED",
                        comparison_operator="GREATER_THAN",
                        threshold=100,
                        threshold_type="PERCENTAGE"
                    ),
                    subscribers=[
                        budgets.CfnBudget.SubscriberProperty(
                            subscription_type="EMAIL",
                            address="admin@example.com"  # Replace with actual email
                        )
                    ]
                )
            ]
        )
        
        # Service-specific budgets
        services = ["Lambda", "EC2-Instance", "CloudWatch", "S3"]
        for service in services:
            budgets.CfnBudget(
                self, f"{service}Budget",
                budget=budgets.CfnBudget.BudgetDataProperty(
                    budget_name=f"observability-{service.lower()}-budget-{self.env_name}",
                    budget_type="COST",
                    time_unit="MONTHLY",
                    budget_limit=budgets.CfnBudget.SpendProperty(
                        amount=200 if self.env_name == "prod" else 20,
                        unit="USD"
                    ),
                    cost_filters=budgets.CfnBudget.CostFiltersProperty(
                        service=[service],
                        tag_key=["Environment"],
                        tag_value=[self.env_name]
                    )
                ),
                notifications_with_subscribers=[
                    budgets.CfnBudget.NotificationWithSubscribersProperty(
                        notification=budgets.CfnBudget.NotificationProperty(
                            notification_type="ACTUAL",
                            comparison_operator="GREATER_THAN",
                            threshold=90,
                            threshold_type="PERCENTAGE"
                        ),
                        subscribers=[
                            budgets.CfnBudget.SubscriberProperty(
                                subscription_type="EMAIL",
                                address="admin@example.com"
                            )
                        ]
                    )
                ]
            )
    
    def _create_cost_anomaly_detector(self):
        """Create cost anomaly detection"""
        
        cost_anomaly_function = lambda_.Function(
            self, "CostAnomalyDetector",
            runtime=lambda_.Runtime.PYTHON_3_9,
            handler="cost_anomaly.handler",
            code=lambda_.Code.from_inline("""
import boto3
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any

logger = logging.getLogger()
logger.setLevel(logging.INFO)

ce = boto3.client('ce')  # Cost Explorer
cloudwatch = boto3.client('cloudwatch')
sns = boto3.client('sns')

def handler(event, context):
    try:
        # Get cost data for anomaly detection
        cost_data = get_cost_data()
        
        # Detect anomalies
        anomalies = detect_cost_anomalies(cost_data)
        
        # Send alerts for anomalies
        for anomaly in anomalies:
            send_cost_alert(anomaly)
        
        # Send metrics to CloudWatch
        send_cost_metrics(cost_data)
        
        return {
            'statusCode': 200,
            'anomalies_detected': len(anomalies)
        }
        
    except Exception as e:
        logger.error(f"Error in cost anomaly detection: {str(e)}")
        return {'statusCode': 500, 'error': str(e)}

def get_cost_data() -> Dict[str, Any]:
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=30)
    
    # Get daily costs for the last 30 days
    response = ce.get_cost_and_usage(
        TimePeriod={
            'Start': start_date.strftime('%Y-%m-%d'),
            'End': end_date.strftime('%Y-%m-%d')
        },
        Granularity='DAILY',
        Metrics=['BlendedCost'],
        GroupBy=[
            {'Type': 'DIMENSION', 'Key': 'SERVICE'}
        ]
    )
    
    return response

def detect_cost_anomalies(cost_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    anomalies = []
    
    # Simple anomaly detection based on daily cost spikes
    daily_costs = {}
    
    for result in cost_data['ResultsByTime']:
        date = result['TimePeriod']['Start']
        total_cost = float(result['Total']['BlendedCost']['Amount'])
        daily_costs[date] = total_cost
    
    # Calculate average and detect spikes
    costs = list(daily_costs.values())
    if len(costs) < 7:
        return anomalies
    
    avg_cost = sum(costs) / len(costs)
    std_dev = (sum((x - avg_cost) ** 2 for x in costs) / len(costs)) ** 0.5
    
    threshold = avg_cost + (2 * std_dev)  # 2 standard deviations
    
    for date, cost in daily_costs.items():
        if cost > threshold:
            anomalies.append({
                'date': date,
                'cost': cost,
                'average': avg_cost,
                'threshold': threshold,
                'severity': 'high' if cost > threshold * 1.5 else 'medium'
            })
    
    return anomalies

def send_cost_alert(anomaly: Dict[str, Any]):
    topic_arn = os.environ.get('COST_ALERT_TOPIC_ARN')
    if not topic_arn:
        return
    
    message = "Cost Anomaly Detected!\n\n" + \
              f"Date: {anomaly['date']}\n" + \
              f"Actual Cost: ${anomaly['cost']:.2f}\n" + \
              f"Average Cost: ${anomaly['average']:.2f}\n" + \
              f"Threshold: ${anomaly['threshold']:.2f}\n" + \
              f"Severity: {anomaly['severity']}\n\n" + \
              "Please review your AWS usage for this date."
    
    sns.publish(
        TopicArn=topic_arn,
        Message=message,
        Subject="Cost Anomaly Alert - " + anomaly['date']
    )

def send_cost_metrics(cost_data: Dict[str, Any]):
    # Send cost metrics to CloudWatch
    metric_data = []
    
    for result in cost_data['ResultsByTime']:
        date = result['TimePeriod']['Start']
        total_cost = float(result['Total']['BlendedCost']['Amount'])
        
        metric_data.append({
            'MetricName': 'DailyCost',
            'Value': total_cost,
            'Unit': 'None',
            'Timestamp': datetime.strptime(date, '%Y-%m-%d')
        })
        
        # Service-specific costs
        for group in result['Groups']:
            service = group['Keys'][0]
            service_cost = float(group['Metrics']['BlendedCost']['Amount'])
            
            metric_data.append({
                'MetricName': 'ServiceCost',
                'Value': service_cost,
                'Unit': 'None',
                'Timestamp': datetime.strptime(date, '%Y-%m-%d'),
                'Dimensions': [
                    {'Name': 'Service', 'Value': service}
                ]
            })
    
    # Send metrics in batches
    for i in range(0, len(metric_data), 20):
        batch = metric_data[i:i+20]
        cloudwatch.put_metric_data(
            Namespace='Observability/Cost',
            MetricData=batch
        )
"""),
            role=self.core_resources["lambda_role"],
            timeout=Duration.minutes(5),
            log_group=self.core_resources["log_groups"]["cost_monitor_logs"],
            tracing=lambda_.Tracing.ACTIVE,
            environment={
                "COST_ALERT_TOPIC_ARN": "arn:aws:sns:us-east-1:123456789012:cost-alerts"  # Replace with actual ARN
            }
        )
        
        # Schedule cost anomaly detection
        events.Rule(
            self, "CostAnomalySchedule",
            schedule=events.Schedule.rate(Duration.hours(6)),
            targets=[targets.LambdaFunction(cost_anomaly_function)]
        )
        
        self.cost_resources["anomaly_detector"] = cost_anomaly_function
    
    def _create_cost_optimizer(self):
        """Create cost optimization recommendations"""
        
        cost_optimizer = lambda_.Function(
            self, "CostOptimizer",
            runtime=lambda_.Runtime.PYTHON_3_9,
            handler="cost_optimizer.handler",
            code=lambda_.Code.from_inline("""
import boto3
import json
import logging
from datetime import datetime, timedelta

logger = logging.getLogger()
logger.setLevel(logging.INFO)

ec2 = boto3.client('ec2')
cloudwatch = boto3.client('cloudwatch')
ce = boto3.client('ce')

def handler(event, context):
    try:
        recommendations = []
        
        # Check for underutilized EC2 instances
        recommendations.extend(check_underutilized_ec2())
        
        # Check for unused EBS volumes
        recommendations.extend(check_unused_ebs_volumes())
        
        # Check for old snapshots
        recommendations.extend(check_old_snapshots())
        
        # Send recommendations
        if recommendations:
            send_optimization_report(recommendations)
        
        return {
            'statusCode': 200,
            'recommendations': len(recommendations)
        }
        
    except Exception as e:
        logger.error(f"Error in cost optimization: {str(e)}")
        return {'statusCode': 500, 'error': str(e)}

def check_underutilized_ec2():
    recommendations = []
    
    # Get running instances
    instances = ec2.describe_instances(
        Filters=[{'Name': 'instance-state-name', 'Values': ['running']}]
    )
    
    for reservation in instances['Reservations']:
        for instance in reservation['Instances']:
            instance_id = instance['InstanceId']
            
            # Check CPU utilization
            cpu_util = get_average_cpu_utilization(instance_id)
            
            if cpu_util < 10:  # Less than 10% average CPU
                recommendations.append({
                    'type': 'underutilized_ec2',
                    'resource_id': instance_id,
                    'instance_type': instance['InstanceType'],
                    'cpu_utilization': cpu_util,
                    'recommendation': 'Consider downsizing or terminating this instance',
                    'potential_savings': estimate_ec2_savings(instance['InstanceType'])
                })
    
    return recommendations

def check_unused_ebs_volumes():
    recommendations = []
    
    # Get unattached volumes
    volumes = ec2.describe_volumes(
        Filters=[{'Name': 'status', 'Values': ['available']}]
    )
    
    for volume in volumes['Volumes']:
        volume_id = volume['VolumeId']
        size = volume['Size']
        volume_type = volume['VolumeType']
        
        recommendations.append({
            'type': 'unused_ebs_volume',
            'resource_id': volume_id,
            'size_gb': size,
            'volume_type': volume_type,
            'recommendation': 'Delete unused EBS volume',
            'potential_savings': estimate_ebs_savings(size, volume_type)
        })
    
    return recommendations

def check_old_snapshots():
    recommendations = []
    
    # Get snapshots older than 30 days
    cutoff_date = datetime.now() - timedelta(days=30)
    
    snapshots = ec2.describe_snapshots(OwnerIds=['self'])
    
    for snapshot in snapshots['Snapshots']:
        start_time = snapshot['StartTime'].replace(tzinfo=None)
        
        if start_time < cutoff_date:
            recommendations.append({
                'type': 'old_snapshot',
                'resource_id': snapshot['SnapshotId'],
                'age_days': (datetime.now() - start_time).days,
                'recommendation': 'Consider deleting old snapshot',
                'potential_savings': 5  # Estimated monthly savings
            })
    
    return recommendations

def get_average_cpu_utilization(instance_id: str) -> float:
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(days=7)
    
    try:
        response = cloudwatch.get_metric_statistics(
            Namespace='AWS/EC2',
            MetricName='CPUUtilization',
            Dimensions=[{'Name': 'InstanceId', 'Value': instance_id}],
            StartTime=start_time,
            EndTime=end_time,
            Period=3600,  # 1 hour
            Statistics=['Average']
        )
        
        if response['Datapoints']:
            return sum(point['Average'] for point in response['Datapoints']) / len(response['Datapoints'])
        
    except Exception as e:
        logger.warning(f"Could not get CPU metrics for {instance_id}: {e}")
    
    return 50  # Default to 50% if no data

def estimate_ec2_savings(instance_type: str) -> float:
    # Simplified cost estimation
    cost_map = {
        't2.micro': 8.5,
        't2.small': 17,
        't2.medium': 34,
        't3.micro': 7.5,
        't3.small': 15,
        't3.medium': 30
    }
    return cost_map.get(instance_type, 50)

def estimate_ebs_savings(size_gb: int, volume_type: str) -> float:
    # Simplified EBS cost estimation per month
    cost_per_gb = {
        'gp2': 0.10,
        'gp3': 0.08,
        'io1': 0.125,
        'io2': 0.125
    }
    return size_gb * cost_per_gb.get(volume_type, 0.10)

def send_optimization_report(recommendations):
    # In a real implementation, this would send to SNS or save to S3
    logger.info(f"Cost optimization recommendations: {json.dumps(recommendations, indent=2)}")
"""),
            role=self.core_resources["lambda_role"],
            timeout=Duration.minutes(10),
            log_group=self.core_resources["log_groups"]["cost_monitor_logs"],
            tracing=lambda_.Tracing.ACTIVE
        )
        
        # Schedule cost optimization checks
        events.Rule(
            self, "CostOptimizationSchedule",
            schedule=events.Schedule.rate(Duration.days(1)),
            targets=[targets.LambdaFunction(cost_optimizer)]
        )
        
        self.cost_resources["optimizer"] = cost_optimizer
    
    def _create_cost_dashboard(self):
        """Create cost monitoring dashboard"""
        
        self.cost_resources["dashboard"] = cloudwatch.Dashboard(
            self, "CostDashboard",
            dashboard_name=f"Observability-Cost-{self.env_name}",
            widgets=[
                [
                    cloudwatch.GraphWidget(
                        title="Daily Cost Trend",
                        left=[
                            cloudwatch.Metric(
                                namespace="Observability/Cost",
                                metric_name="DailyCost",
                                statistic="Sum",
                                period=Duration.days(1)
                            )
                        ],
                        width=12,
                        height=6
                    ),
                    cloudwatch.SingleValueWidget(
                        title="Current Month Cost",
                        metrics=[
                            cloudwatch.Metric(
                                namespace="Observability/Cost",
                                metric_name="DailyCost",
                                statistic="Sum",
                                period=Duration.days(30)
                            )
                        ],
                        width=12,
                        height=6
                    )
                ],
                [
                    cloudwatch.GraphWidget(
                        title="Cost by Service",
                        left=[
                            cloudwatch.Metric(
                                namespace="Observability/Cost",
                                metric_name="ServiceCost",
                                statistic="Sum",
                                period=Duration.days(1)
                            )
                        ],
                        width=24,
                        height=8
                    )
                ]
            ]
        )