from aws_cdk import (
    Stack,
    aws_lambda as lambda_,
    aws_events as events,
    aws_events_targets as targets,
    aws_logs as logs,
    aws_logs_destinations as destinations,
    aws_kinesis as kinesis,
    aws_kinesisfirehose as firehose,
    aws_s3 as s3,
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
        
        # Kinesis stream for log data
        self.log_resources["stream"] = kinesis.Stream(
            self, "LogStream",
            stream_name=f"observability-logs-{self.env_name}",
            shard_count=2 if self.env_name == "prod" else 1,
            encryption=kinesis.StreamEncryption.KMS,
            encryption_key=self.core_resources["kms_key"]
        )
        
        # Kinesis Firehose for S3 delivery
        self.log_resources["firehose"] = firehose.CfnDeliveryStream(
            self, "LogFirehose",
            delivery_stream_name=f"observability-logs-firehose-{self.env_name}",
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
                role_arn=self.core_resources["lambda_role"].role_arn,
                processing_configuration=firehose.CfnDeliveryStream.ProcessingConfigurationProperty(
                    enabled=True,
                    processors=[
                        firehose.CfnDeliveryStream.ProcessorProperty(
                            type="Lambda",
                            parameters=[
                                firehose.CfnDeliveryStream.ProcessorParameterProperty(
                                    parameter_name="LambdaArn",
                                    parameter_value="arn:aws:lambda:region:account:function:log-processor"
                                )
                            ]
                        )
                    ]
                )
            )
        )
    
    def _create_log_processor(self):
        """Create Lambda function for log processing and enrichment"""
        
        self.log_resources["processor"] = lambda_.Function(
            self, "LogProcessor",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="log_processor.handler",
            code=lambda_.Code.from_inline("""
import json
import base64
import gzip
import logging
import re
from datetime import datetime
from typing import Dict, List, Any

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def handler(event, context):
    output = []
    
    for record in event['records']:
        try:
            # Decode and decompress the log data
            compressed_payload = base64.b64decode(record['data'])
            uncompressed_payload = gzip.decompress(compressed_payload)
            log_data = json.loads(uncompressed_payload)
            
            # Process each log event
            processed_events = []
            for log_event in log_data.get('logEvents', []):
                processed_event = process_log_event(log_event, log_data)
                if processed_event:
                    processed_events.append(processed_event)
            
            # Create output record
            if processed_events:
                output_data = {
                    'logGroup': log_data.get('logGroup'),
                    'logStream': log_data.get('logStream'),
                    'processedEvents': processed_events,
                    'processingTimestamp': datetime.utcnow().isoformat()
                }
                
                output_record = {
                    'recordId': record['recordId'],
                    'result': 'Ok',
                    'data': base64.b64encode(
                        json.dumps(output_data).encode('utf-8')
                    ).decode('utf-8')
                }
            else:
                # Skip empty records
                output_record = {
                    'recordId': record['recordId'],
                    'result': 'ProcessingFailed'
                }
            
            output.append(output_record)
            
        except Exception as e:
            logger.error(f"Error processing record: {str(e)}")
            output.append({
                'recordId': record['recordId'],
                'result': 'ProcessingFailed'
            })
    
    return {'records': output}

def process_log_event(log_event: Dict[str, Any], log_data: Dict[str, Any]) -> Dict[str, Any]:
    message = log_event.get('message', '')
    timestamp = log_event.get('timestamp')
    
    # Extract structured information from log message
    processed_event = {
        'timestamp': timestamp,
        'message': message,
        'logGroup': log_data.get('logGroup'),
        'logStream': log_data.get('logStream'),
        'level': extract_log_level(message),
        'error_type': extract_error_type(message),
        'request_id': extract_request_id(message),
        'duration': extract_duration(message),
        'memory_used': extract_memory_usage(message),
        'anomaly_score': calculate_anomaly_score(message)
    }
    
    # Add custom fields based on log source
    if 'lambda' in log_data.get('logGroup', '').lower():
        processed_event.update(process_lambda_log(message))
    elif 'api-gateway' in log_data.get('logGroup', '').lower():
        processed_event.update(process_api_gateway_log(message))
    
    return processed_event

def extract_log_level(message: str) -> str:
    levels = ['ERROR', 'WARN', 'INFO', 'DEBUG', 'TRACE']
    for level in levels:
        if level in message.upper():
            return level
    return 'UNKNOWN'

def extract_error_type(message: str) -> str:
    error_patterns = [
        r'(\w+Exception)',
        r'(\w+Error)',
        r'HTTP (\d{3})',
        r'Status: (\d{3})'
    ]
    
    for pattern in error_patterns:
        match = re.search(pattern, message)
        if match:
            return match.group(1)
    
    return None

def extract_request_id(message: str) -> str:
    patterns = [
        r'RequestId: ([a-f0-9-]+)',
        r'request_id[=:]([a-f0-9-]+)',
        r'correlation[_-]id[=:]([a-f0-9-]+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, message, re.IGNORECASE)
        if match:
            return match.group(1)
    
    return None

def extract_duration(message: str) -> float:
    patterns = [
        r'Duration: ([\d.]+) ms',
        r'took ([\d.]+)ms',
        r'elapsed: ([\d.]+)ms'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, message, re.IGNORECASE)
        if match:
            return float(match.group(1))
    
    return None

def extract_memory_usage(message: str) -> float:
    patterns = [
        r'Memory Used: ([\d.]+) MB',
        r'memory[_-]used[=:] ([\d.]+)',
        r'heap[_-]size[=:] ([\d.]+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, message, re.IGNORECASE)
        if match:
            return float(match.group(1))
    
    return None

def calculate_anomaly_score(message: str) -> float:
    # Simple anomaly scoring based on keywords
    anomaly_keywords = {
        'error': 0.8,
        'exception': 0.9,
        'timeout': 0.7,
        'failed': 0.6,
        'critical': 0.9,
        'alert': 0.5
    }
    
    score = 0.0
    message_lower = message.lower()
    
    for keyword, weight in anomaly_keywords.items():
        if keyword in message_lower:
            score = max(score, weight)
    
    return score

def process_lambda_log(message: str) -> Dict[str, Any]:
    # Lambda-specific processing
    fields = {}
    
    # Extract cold start information
    if 'INIT_START' in message:
        fields['cold_start'] = True
    
    # Extract billing information
    billing_match = re.search(r'Billed Duration: ([\d.]+) ms', message)
    if billing_match:
        fields['billed_duration'] = float(billing_match.group(1))
    
    return fields

def process_api_gateway_log(message: str) -> Dict[str, Any]:
    # API Gateway-specific processing
    fields = {}
    
    # Extract HTTP method and path
    http_match = re.search(r'(GET|POST|PUT|DELETE|PATCH) (/\S*)', message)
    if http_match:
        fields['http_method'] = http_match.group(1)
        fields['http_path'] = http_match.group(2)
    
    # Extract response time
    response_time_match = re.search(r'responseTime: ([\d.]+)', message)
    if response_time_match:
        fields['response_time'] = float(response_time_match.group(1))
    
    return fields
"""),
            role=self.core_resources["lambda_role"],
            timeout=Duration.minutes(5),
            memory_size=512,
            log_group=self.core_resources["log_groups"]["platform_logs"],
            tracing=lambda_.Tracing.ACTIVE
        )
    
    def _create_log_insights_queries(self):
        """Create scheduled CloudWatch Logs Insights queries"""
        
        insights_runner = lambda_.Function(
            self, "LogInsightsRunner",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="log_insights.handler",
            code=lambda_.Code.from_inline("""
import boto3
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List

logger = logging.getLogger()
logger.setLevel(logging.INFO)

logs_client = boto3.client('logs')
cloudwatch = boto3.client('cloudwatch')

def handler(event, context):
    try:
        # Run predefined queries
        queries = get_predefined_queries()
        
        results = {}
        for query_name, query_config in queries.items():
            result = run_insights_query(query_name, query_config)
            results[query_name] = result
            
            # Send metrics based on results
            send_query_metrics(query_name, result)
        
        return {
            'statusCode': 200,
            'results': results
        }
        
    except Exception as e:
        logger.error(f"Error running log insights: {str(e)}")
        return {'statusCode': 500, 'error': str(e)}

def get_predefined_queries() -> Dict[str, Dict]:
    return {
        'error_analysis': {
            'query': '''
                fields @timestamp, @message
                | filter @message like /ERROR/
                | stats count() by bin(5m)
                | sort @timestamp desc
            ''',
            'log_groups': ['/aws/lambda/*', '/aws/apigateway/*'],
            'time_range_hours': 1
        },
        'performance_analysis': {
            'query': '''
                fields @timestamp, @duration
                | filter @type = "REPORT"
                | stats avg(@duration), max(@duration), min(@duration) by bin(5m)
                | sort @timestamp desc
            ''',
            'log_groups': ['/aws/lambda/*'],
            'time_range_hours': 1
        },
        'high_memory_usage': {
            'query': '''
                fields @timestamp, @message, @memorySize, @maxMemoryUsed
                | filter @type = "REPORT"
                | filter @maxMemoryUsed / @memorySize > 0.8
                | sort @timestamp desc
                | limit 20
            ''',
            'log_groups': ['/aws/lambda/*'],
            'time_range_hours': 6
        },
        'api_errors': {
            'query': '''
                fields @timestamp, @message
                | filter @message like /5\d\d/ or @message like /4\d\d/
                | stats count() by bin(5m)
                | sort @timestamp desc
            ''',
            'log_groups': ['/aws/apigateway/*'],
            'time_range_hours': 1
        }
    }

def run_insights_query(query_name: str, query_config: Dict) -> Dict:
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(hours=query_config['time_range_hours'])
    
    try:
        # Start query
        response = logs_client.start_query(
            logGroupNames=query_config['log_groups'],
            startTime=int(start_time.timestamp()),
            endTime=int(end_time.timestamp()),
            queryString=query_config['query']
        )
        
        query_id = response['queryId']
        
        # Wait for query to complete (simplified - in production use polling)
        import time
        time.sleep(10)
        
        # Get results
        results = logs_client.get_query_results(queryId=query_id)
        
        return {
            'status': results['status'],
            'results': results.get('results', []),
            'statistics': results.get('statistics', {})
        }
        
    except Exception as e:
        logger.error(f"Error running query {query_name}: {str(e)}")
        return {'status': 'Failed', 'error': str(e)}

def send_query_metrics(query_name: str, result: Dict):
    if result['status'] != 'Complete':
        return
    
    # Extract metrics from query results
    result_count = len(result.get('results', []))
    
    cloudwatch.put_metric_data(
        Namespace='Observability/LogInsights',
        MetricData=[
            {
                'MetricName': 'QueryResultCount',
                'Value': result_count,
                'Dimensions': [
                    {'Name': 'QueryName', 'Value': query_name}
                ]
            }
        ]
    )
    
    # Send specific metrics based on query type
    if query_name == 'error_analysis' and result_count > 0:
        cloudwatch.put_metric_data(
            Namespace='Observability/LogInsights',
            MetricData=[
                {
                    'MetricName': 'ErrorCount',
                    'Value': result_count,
                    'Unit': 'Count'
                }
            ]
        )
"""),
            role=self.core_resources["lambda_role"],
            timeout=Duration.minutes(10),
            log_group=self.core_resources["log_groups"]["platform_logs"],
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
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="log_anomaly.handler",
            code=lambda_.Code.from_inline("""
import boto3
import json
import logging
from datetime import datetime, timedelta
from collections import defaultdict
import re

logger = logging.getLogger()
logger.setLevel(logging.INFO)

logs_client = boto3.client('logs')
cloudwatch = boto3.client('cloudwatch')
events = boto3.client('events')

def handler(event, context):
    try:
        # Analyze logs for anomalies
        anomalies = detect_log_anomalies()
        
        # Send alerts for detected anomalies
        for anomaly in anomalies:
            send_anomaly_alert(anomaly)
        
        return {
            'statusCode': 200,
            'anomalies_detected': len(anomalies)
        }
        
    except Exception as e:
        logger.error(f"Error in log anomaly detection: {str(e)}")
        return {'statusCode': 500, 'error': str(e)}

def detect_log_anomalies():
    anomalies = []
    
    # Get log groups to analyze
    log_groups = get_monitored_log_groups()
    
    for log_group in log_groups:
        # Analyze error patterns
        error_anomalies = detect_error_anomalies(log_group)
        anomalies.extend(error_anomalies)
        
        # Analyze volume anomalies
        volume_anomalies = detect_volume_anomalies(log_group)
        anomalies.extend(volume_anomalies)
        
        # Analyze new error patterns
        new_error_anomalies = detect_new_error_patterns(log_group)
        anomalies.extend(new_error_anomalies)
    
    return anomalies

def get_monitored_log_groups():
    # Get list of log groups to monitor
    response = logs_client.describe_log_groups()
    
    # Filter for application log groups
    monitored_groups = []
    for log_group in response['logGroups']:
        name = log_group['logGroupName']
        if any(pattern in name for pattern in ['/aws/lambda/', '/aws/apigateway/', '/aws/ecs/']):
            monitored_groups.append(name)
    
    return monitored_groups

def detect_error_anomalies(log_group: str):
    anomalies = []
    
    # Get error counts for the last hour vs previous hours
    current_hour_errors = get_error_count(log_group, hours_back=1)
    previous_hours_errors = [
        get_error_count(log_group, hours_back=i) 
        for i in range(2, 25)  # Previous 23 hours
    ]
    
    if not previous_hours_errors:
        return anomalies
    
    avg_errors = sum(previous_hours_errors) / len(previous_hours_errors)
    std_dev = (sum((x - avg_errors) ** 2 for x in previous_hours_errors) / len(previous_hours_errors)) ** 0.5
    
    threshold = avg_errors + (2 * std_dev)
    
    if current_hour_errors > threshold and current_hour_errors > 10:
        anomalies.append({
            'type': 'error_spike',
            'log_group': log_group,
            'current_errors': current_hour_errors,
            'average_errors': avg_errors,
            'threshold': threshold,
            'severity': 'high' if current_hour_errors > threshold * 2 else 'medium'
        })
    
    return anomalies

def detect_volume_anomalies(log_group: str):
    anomalies = []
    
    # Similar logic for log volume anomalies
    current_volume = get_log_volume(log_group, hours_back=1)
    previous_volumes = [
        get_log_volume(log_group, hours_back=i)
        for i in range(2, 25)
    ]
    
    if not previous_volumes:
        return anomalies
    
    avg_volume = sum(previous_volumes) / len(previous_volumes)
    
    # Check for significant volume changes
    if current_volume > avg_volume * 3:  # 3x increase
        anomalies.append({
            'type': 'volume_spike',
            'log_group': log_group,
            'current_volume': current_volume,
            'average_volume': avg_volume,
            'severity': 'medium'
        })
    elif current_volume < avg_volume * 0.1 and avg_volume > 100:  # 90% decrease
        anomalies.append({
            'type': 'volume_drop',
            'log_group': log_group,
            'current_volume': current_volume,
            'average_volume': avg_volume,
            'severity': 'medium'
        })
    
    return anomalies

def detect_new_error_patterns(log_group: str):
    anomalies = []
    
    # Get recent error messages
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(hours=1)
    
    try:
        response = logs_client.start_query(
            logGroupName=log_group,
            startTime=int(start_time.timestamp()),
            endTime=int(end_time.timestamp()),
            queryString='''
                fields @timestamp, @message
                | filter @message like /ERROR/ or @message like /Exception/
                | limit 100
            '''
        )
        
        # In a real implementation, you'd wait for the query and analyze patterns
        # This is simplified for the example
        
    except Exception as e:
        logger.warning(f"Could not analyze error patterns for {log_group}: {e}")
    
    return anomalies

def get_error_count(log_group: str, hours_back: int) -> int:
    end_time = datetime.utcnow() - timedelta(hours=hours_back-1)
    start_time = end_time - timedelta(hours=1)
    
    try:
        response = logs_client.start_query(
            logGroupName=log_group,
            startTime=int(start_time.timestamp()),
            endTime=int(end_time.timestamp()),
            queryString='fields @message | filter @message like /ERROR/ | stats count()'
        )
        
        # Simplified - in reality you'd wait for the query to complete
        return 0
        
    except Exception:
        return 0

def get_log_volume(log_group: str, hours_back: int) -> int:
    end_time = datetime.utcnow() - timedelta(hours=hours_back-1)
    start_time = end_time - timedelta(hours=1)
    
    try:
        response = logs_client.start_query(
            logGroupName=log_group,
            startTime=int(start_time.timestamp()),
            endTime=int(end_time.timestamp()),
            queryString='fields @message | stats count()'
        )
        
        # Simplified - in reality you'd wait for the query to complete
        return 0
        
    except Exception:
        return 0

def send_anomaly_alert(anomaly):
    # Send anomaly to EventBridge for further processing
    events.put_events(
        Entries=[
            {
                'Source': 'observability.logs',
                'DetailType': 'Log Anomaly Detected',
                'Detail': json.dumps(anomaly),
                'EventBusName': os.environ.get('EVENT_BUS_NAME')
            }
        ]
    )
    
    logger.info(f"Log anomaly detected: {anomaly}")
"""),
            role=self.core_resources["lambda_role"],
            timeout=Duration.minutes(10),
            log_group=self.core_resources["log_groups"]["platform_logs"],
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