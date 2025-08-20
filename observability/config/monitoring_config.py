from typing import Dict, List, Optional
from pydantic import BaseModel

class MetricConfig(BaseModel):
    namespace: str
    metric_name: str
    dimensions: Dict[str, str]
    statistic: str = "Average"
    period: int = 300

class AlertConfig(BaseModel):
    name: str
    description: str
    metric: MetricConfig
    threshold: float
    comparison_operator: str
    evaluation_periods: int = 2
    datapoints_to_alarm: int = 2

class ServiceConfig(BaseModel):
    service_name: str
    metrics: List[MetricConfig]
    alerts: List[AlertConfig]
    log_groups: List[str]

class MonitoringConfig:
    # Default metrics for AWS services
    EC2_METRICS = [
        MetricConfig(namespace="AWS/EC2", metric_name="CPUUtilization", dimensions={"InstanceId": "*"}),
        MetricConfig(namespace="AWS/EC2", metric_name="NetworkIn", dimensions={"InstanceId": "*"}),
        MetricConfig(namespace="AWS/EC2", metric_name="NetworkOut", dimensions={"InstanceId": "*"}),
        MetricConfig(namespace="AWS/EC2", metric_name="DiskReadOps", dimensions={"InstanceId": "*"}),
        MetricConfig(namespace="AWS/EC2", metric_name="DiskWriteOps", dimensions={"InstanceId": "*"})
    ]
    
    LAMBDA_METRICS = [
        MetricConfig(namespace="AWS/Lambda", metric_name="Duration", dimensions={"FunctionName": "*"}),
        MetricConfig(namespace="AWS/Lambda", metric_name="Errors", dimensions={"FunctionName": "*"}),
        MetricConfig(namespace="AWS/Lambda", metric_name="Invocations", dimensions={"FunctionName": "*"}),
        MetricConfig(namespace="AWS/Lambda", metric_name="Throttles", dimensions={"FunctionName": "*"}),
        MetricConfig(namespace="AWS/Lambda", metric_name="ConcurrentExecutions", dimensions={"FunctionName": "*"})
    ]
    
    RDS_METRICS = [
        MetricConfig(namespace="AWS/RDS", metric_name="CPUUtilization", dimensions={"DBInstanceIdentifier": "*"}),
        MetricConfig(namespace="AWS/RDS", metric_name="DatabaseConnections", dimensions={"DBInstanceIdentifier": "*"}),
        MetricConfig(namespace="AWS/RDS", metric_name="FreeableMemory", dimensions={"DBInstanceIdentifier": "*"}),
        MetricConfig(namespace="AWS/RDS", metric_name="ReadLatency", dimensions={"DBInstanceIdentifier": "*"}),
        MetricConfig(namespace="AWS/RDS", metric_name="WriteLatency", dimensions={"DBInstanceIdentifier": "*"})
    ]
    
    ECS_METRICS = [
        MetricConfig(namespace="AWS/ECS", metric_name="CPUUtilization", dimensions={"ServiceName": "*", "ClusterName": "*"}),
        MetricConfig(namespace="AWS/ECS", metric_name="MemoryUtilization", dimensions={"ServiceName": "*", "ClusterName": "*"}),
        MetricConfig(namespace="AWS/ECS", metric_name="RunningTaskCount", dimensions={"ServiceName": "*", "ClusterName": "*"})
    ]
    
    # Default alert thresholds
    DEFAULT_ALERTS = {
        "high_cpu": AlertConfig(
            name="HighCPUUtilization",
            description="CPU utilization is above 80%",
            metric=MetricConfig(namespace="AWS/EC2", metric_name="CPUUtilization", dimensions={"InstanceId": "*"}),
            threshold=80.0,
            comparison_operator="GreaterThanThreshold"
        ),
        "high_error_rate": AlertConfig(
            name="HighErrorRate",
            description="Error rate is above 5%",
            metric=MetricConfig(namespace="AWS/Lambda", metric_name="Errors", dimensions={"FunctionName": "*"}),
            threshold=5.0,
            comparison_operator="GreaterThanThreshold"
        )
    }
    
    @classmethod
    def get_service_config(cls, service_type: str) -> Optional[ServiceConfig]:
        configs = {
            "ec2": ServiceConfig(
                service_name="EC2",
                metrics=cls.EC2_METRICS,
                alerts=[cls.DEFAULT_ALERTS["high_cpu"]],
                log_groups=["/aws/ec2/*"]
            ),
            "lambda": ServiceConfig(
                service_name="Lambda",
                metrics=cls.LAMBDA_METRICS,
                alerts=[cls.DEFAULT_ALERTS["high_error_rate"]],
                log_groups=["/aws/lambda/*"]
            ),
            "rds": ServiceConfig(
                service_name="RDS",
                metrics=cls.RDS_METRICS,
                alerts=[],
                log_groups=["/aws/rds/*"]
            ),
            "ecs": ServiceConfig(
                service_name="ECS",
                metrics=cls.ECS_METRICS,
                alerts=[],
                log_groups=["/aws/ecs/*"]
            )
        }
        return configs.get(service_type)