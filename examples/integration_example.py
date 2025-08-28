"""
Example: Adding observability to an existing CDK project
"""
from aws_cdk import Stack, aws_lambda as lambda_
from constructs import Construct

# Import our reusable constructs
from src.constructs.monitoring_construct import MonitoringConstruct
from src.constructs.lambda_monitoring_construct import LambdaMonitoringConstruct

class ExistingAppStack(Stack):
    """Example of integrating observability into existing infrastructure"""
    
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        # Your existing Lambda function
        my_lambda = lambda_.Function(
            self, "MyBusinessLogic",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="index.handler",
            code=lambda_.Code.from_asset("my_lambda_code")
        )
        
        # Add comprehensive monitoring with ONE construct
        LambdaMonitoringConstruct(
            self, "MyLambdaMonitoring",
            lambda_function=my_lambda,
            environment="prod",
            alert_topic=None  # Will create default topics
        )
        
        # That's it! You now have:
        # - CloudWatch dashboard
        # - Error rate alarms
        # - Duration alarms  
        # - Throttling alarms
        # - SNS notifications
        # - X-Ray tracing integration

# Alternative: Use the generic monitoring construct
class AnotherAppStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        # Add monitoring for any service with custom metrics
        MonitoringConstruct(
            self, "CustomServiceMonitoring",
            service_name="PaymentProcessor",
            environment="prod",
            alert_topic=None,  # Auto-created
            metrics_config=[
                {
                    'namespace': 'MyApp/Payments',
                    'metric_name': 'ProcessedPayments',
                    'alarm': {
                        'threshold': 100,
                        'description': 'Low payment processing rate'
                    }
                }
            ]
        )