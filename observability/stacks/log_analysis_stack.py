from aws_cdk import (
    Stack,
    aws_lambda as lambda_,
    aws_events as events,
    aws_events_targets as targets,
    aws_logs as logs,
    aws_kinesis as kinesis,
    aws_kinesisfirehose as firehose,
    aws_cloudwatch as cloudwatch,
    Duration
)
from constructs import Construct
from typing import Dict, Any

class LogAnalysisStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, environment: str, core_resources: Dict[str, Any], **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        self.env_name = environment
        self.core_resources = core_resources
        self.log_resources = {}
        
        # Create log analysis components
        self._create_log_stream()
        self._create_log_processor()
        self._create_log_insights_queries()
        self._create_anomaly_detector()
    
    def _create_log_stream(self):
        """Create Kinesis stream for log processing"""
        self.log_resources["stream"] = kinesis.Stream(
            self, "LogStream",
            shard_count=2 if self.env_name == "prod" else 1,
            encryption=kinesis.StreamEncryption.KMS,
            encryption_key=self.core_resources["kms_key"]
        )
        
        # Kinesis Firehose for S3 delivery
        self.log_resources["firehose"] = firehose.CfnDeliveryStream(
            self, "LogFirehose",
            kinesis_stream_source_configuration=firehose.CfnDeliveryStream.KinesisStreamSourceConfigurationProperty(
                kinesis_stream_arn=self.log_resources["stream"].stream_arn,
                role_arn=self.core_resources["lambda_role"].role_arn
            ),
            extended_s3_destination_configuration=firehose.CfnDeliveryStream.ExtendedS3DestinationConfigurationProperty(
                bucket_arn=self.core_resources["storage_bucket"].bucket_arn,
                prefix="logs/year=!{timestamp:yyyy}/month=!{timestamp:MM}/day=!{timestamp:dd}/hour=!{timestamp:HH}/",
                error_output_prefix="errors/",
                buffering_hints=firehose.CfnDeliveryStream.BufferingHintsProperty(
                    size_in_m_bs=5,
                    interval_in_seconds=300
                ),
                compression_format="GZIP",
                role_arn=self.core_resources["lambda_role"].role_arn
            )
        )
    
    def _create_log_processor(self):
        """Create Lambda function for log processing and enrichment"""
        self.log_resources["processor"] = lambda_.Function(
            self, "LogProcessor",
            runtime=lambda_.Runtime.PYTHON_3_9,
            handler="index.handler",
            code=lambda_.Code.from_inline("""
import json
import base64
import gzip
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def handler(event, context):
    output = []
    
    for record in event.get('records', []):
        try:
            # Basic log processing
            output_record = {
                'recordId': record['recordId'],
                'result': 'Ok',
                'data': record['data']  # Pass through for now
            }
            output.append(output_record)
            
        except Exception as e:
            logger.error(f"Error processing record: {str(e)}")
            output.append({
                'recordId': record['recordId'],
                'result': 'ProcessingFailed'
            })
    
    return {'records': output}
            """),
            role=self.core_resources["lambda_role"],
            timeout=Duration.minutes(5),
            memory_size=512,
            tracing=lambda_.Tracing.ACTIVE
        )
    
    def _create_log_insights_queries(self):
        """Create scheduled CloudWatch Logs Insights queries"""
        insights_runner = lambda_.Function(
            self, "LogInsightsRunner",
            runtime=lambda_.Runtime.PYTHON_3_9,
            handler="index.handler",
            code=lambda_.Code.from_inline("""
import boto3
import json
import logging
from datetime import datetime, timedelta

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def handler(event, context):
    try:
        logs_client = boto3.client('logs')
        
        # Simple error count query
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=1)
        
        # This is a placeholder - in production you'd run actual insights queries
        logger.info("Running log insights queries")
        
        return {
            'statusCode': 200,
            'message': 'Log insights queries completed'
        }
        
    except Exception as e:
        logger.error(f"Error running log insights: {str(e)}")
        return {'statusCode': 500, 'error': str(e)}
            """),
            role=self.core_resources["lambda_role"],
            timeout=Duration.minutes(10),
            tracing=lambda_.Tracing.ACTIVE
        )
        
        # Schedule log insights queries
        events.Rule(
            self, "LogInsightsSchedule",
            schedule=events.Schedule.rate(Duration.minutes(15)),
            targets=[targets.LambdaFunction(insights_runner)]
        )
        
        self.log_resources["insights_runner"] = insights_runner
    
    def _create_anomaly_detector(self):
        """Create log anomaly detection"""
        anomaly_detector = lambda_.Function(
            self, "LogAnomalyDetector",
            runtime=lambda_.Runtime.PYTHON_3_9,
            handler="index.handler",
            code=lambda_.Code.from_inline("""
import boto3
import json
import logging
from datetime import datetime, timedelta

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def handler(event, context):
    try:
        # Basic anomaly detection logic
        logger.info("Running log anomaly detection")
        
        # Placeholder for anomaly detection
        anomalies_detected = 0
        
        return {
            'statusCode': 200,
            'anomalies_detected': anomalies_detected
        }
        
    except Exception as e:
        logger.error(f"Error in log anomaly detection: {str(e)}")
        return {'statusCode': 500, 'error': str(e)}
            """),
            role=self.core_resources["lambda_role"],
            timeout=Duration.minutes(10),
            tracing=lambda_.Tracing.ACTIVE,
            environment={
                "EVENT_BUS_NAME": self.core_resources["event_bus"].event_bus_name
            }
        )
        
        # Schedule anomaly detection
        events.Rule(
            self, "LogAnomalySchedule",
            schedule=events.Schedule.rate(Duration.minutes(30)),
            targets=[targets.LambdaFunction(anomaly_detector)]
        )
        
        self.log_resources["anomaly_detector"] = anomaly_detector