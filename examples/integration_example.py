"""
Example showing how to integrate the observability platform with existing applications
"""
import json
import boto3
import logging
from datetime import datetime
from typing import Dict, Any

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ObservabilityClient:
    """
    Client for integrating with the observability platform
    Provides simple methods to send metrics, logs, and alerts
    """
    
    def __init__(self, environment: str = 'dev'):
        self.environment = environment
        self.cloudwatch = boto3.client('cloudwatch')
        self.events = boto3.client('events')
        self.event_bus_name = f'observability-{environment}'
        self.namespace_prefix = 'CustomApp'
    
    def send_business_metric(
        self, 
        metric_name: str, 
        value: float, 
        unit: str = 'Count',
        dimensions: Dict[str, str] = None
    ):
        """Send a business metric to CloudWatch"""
        try:
            metric_data = {
                'MetricName': metric_name,
                'Value': value,
                'Unit': unit,
                'Timestamp': datetime.utcnow()
            }
            
            if dimensions:
                metric_data['Dimensions'] = [
                    {'Name': k, 'Value': v} for k, v in dimensions.items()
                ]
            
            self.cloudwatch.put_metric_data(
                Namespace=f'{self.namespace_prefix}/Business',
                MetricData=[metric_data]
            )
            
            logger.info(f"Sent metric: {metric_name} = {value}")
            
        except Exception as e:
            logger.error(f"Failed to send metric {metric_name}: {e}")
    
    def send_performance_metric(
        self,
        operation: str,
        duration_ms: float,
        success: bool = True,
        additional_dimensions: Dict[str, str] = None
    ):
        """Send performance metrics for an operation"""
        dimensions = {
            'Operation': operation,
            'Environment': self.environment,
            'Status': 'Success' if success else 'Error'
        }
        
        if additional_dimensions:
            dimensions.update(additional_dimensions)
        
        # Send duration metric
        self.send_business_metric(
            metric_name='OperationDuration',
            value=duration_ms,
            unit='Milliseconds',
            dimensions=dimensions
        )
        
        # Send count metric
        self.send_business_metric(
            metric_name='OperationCount',
            value=1,
            unit='Count',
            dimensions=dimensions
        )
    
    def send_custom_alert(
        self,
        severity: str,
        message: str,
        source: str,
        additional_context: Dict[str, Any] = None
    ):
        """Send a custom alert to the observability platform"""
        try:
            alert_detail = {
                'severity': severity,
                'message': message,
                'source': source,
                'timestamp': datetime.utcnow().isoformat(),
                'environment': self.environment
            }
            
            if additional_context:
                alert_detail['context'] = additional_context
            
            self.events.put_events(
                Entries=[
                    {
                        'Source': f'{source}.alerts',
                        'DetailType': 'Custom Application Alert',
                        'Detail': json.dumps(alert_detail),
                        'EventBusName': self.event_bus_name
                    }
                ]
            )
            
            logger.info(f"Sent {severity} alert: {message}")
            
        except Exception as e:
            logger.error(f"Failed to send alert: {e}")
    
    def log_structured_event(
        self,
        event_type: str,
        **kwargs
    ):
        """Log a structured event for analysis"""
        log_entry = {
            'event_type': event_type,
            'timestamp': datetime.utcnow().isoformat(),
            'environment': self.environment,
            **kwargs
        }
        
        logger.info(json.dumps(log_entry))

# Example usage in different scenarios
class ECommerceApplication:
    """Example e-commerce application with observability integration"""
    
    def __init__(self, environment: str = 'dev'):
        self.observability = ObservabilityClient(environment)
    
    def process_order(self, order_id: str, user_id: str, amount: float):
        """Process an order with observability"""
        start_time = datetime.utcnow()
        
        try:
            # Log the start of order processing
            self.observability.log_structured_event(
                event_type='order_processing_started',
                order_id=order_id,
                user_id=user_id,
                amount=amount
            )
            
            # Simulate order processing
            self._validate_order(order_id, amount)
            self._process_payment(order_id, amount)
            self._update_inventory(order_id)
            self._send_confirmation(user_id, order_id)
            
            # Calculate processing time
            duration = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            # Send performance metrics
            self.observability.send_performance_metric(
                operation='process_order',
                duration_ms=duration,
                success=True,
                additional_dimensions={
                    'OrderValue': self._get_order_value_bucket(amount)
                }
            )
            
            # Send business metrics
            self.observability.send_business_metric(
                metric_name='OrdersProcessed',
                value=1,
                dimensions={
                    'Environment': self.observability.environment,
                    'OrderValue': self._get_order_value_bucket(amount)
                }
            )
            
            self.observability.send_business_metric(
                metric_name='Revenue',
                value=amount,
                unit='None',
                dimensions={'Environment': self.observability.environment}
            )
            
            # Log successful completion
            self.observability.log_structured_event(
                event_type='order_processing_completed',
                order_id=order_id,
                user_id=user_id,
                amount=amount,
                duration_ms=duration
            )
            
            return {'status': 'success', 'order_id': order_id}
            
        except Exception as e:
            # Calculate processing time even for failures
            duration = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            # Send failure metrics
            self.observability.send_performance_metric(
                operation='process_order',
                duration_ms=duration,
                success=False,
                additional_dimensions={
                    'ErrorType': type(e).__name__
                }
            )
            
            # Send custom alert for critical failures
            if isinstance(e, PaymentProcessingError):
                self.observability.send_custom_alert(
                    severity='high',
                    message=f'Payment processing failed for order {order_id}',
                    source='ecommerce-app',
                    additional_context={
                        'order_id': order_id,
                        'user_id': user_id,
                        'amount': amount,
                        'error': str(e)
                    }
                )
            
            # Log the error
            self.observability.log_structured_event(
                event_type='order_processing_failed',
                order_id=order_id,
                user_id=user_id,
                amount=amount,
                error_type=type(e).__name__,
                error_message=str(e),
                duration_ms=duration
            )
            
            raise
    
    def _validate_order(self, order_id: str, amount: float):
        """Validate order details"""
        if amount <= 0:
            raise ValueError("Invalid order amount")
        # Simulate validation logic
    
    def _process_payment(self, order_id: str, amount: float):
        """Process payment"""
        # Simulate payment processing
        import random
        if random.random() < 0.05:  # 5% failure rate
            raise PaymentProcessingError("Payment gateway timeout")
    
    def _update_inventory(self, order_id: str):
        """Update inventory"""
        # Simulate inventory update
        pass
    
    def _send_confirmation(self, user_id: str, order_id: str):
        """Send order confirmation"""
        # Simulate sending confirmation
        pass
    
    def _get_order_value_bucket(self, amount: float) -> str:
        """Categorize order value for metrics"""
        if amount < 50:
            return 'low'
        elif amount < 200:
            return 'medium'
        else:
            return 'high'

class PaymentProcessingError(Exception):
    """Custom exception for payment processing errors"""
    pass

# Example usage
if __name__ == "__main__":
    # Initialize the application
    app = ECommerceApplication(environment='dev')
    
    # Process some sample orders
    sample_orders = [
        {'order_id': 'order-001', 'user_id': 'user-123', 'amount': 99.99},
        {'order_id': 'order-002', 'user_id': 'user-456', 'amount': 249.50},
        {'order_id': 'order-003', 'user_id': 'user-789', 'amount': 15.00},
    ]
    
    for order in sample_orders:
        try:
            result = app.process_order(**order)
            print(f"Order {order['order_id']} processed successfully")
        except Exception as e:
            print(f"Order {order['order_id']} failed: {e}")
    
    # Send some additional business metrics
    observability_client = ObservabilityClient('dev')
    
    # Daily active users
    observability_client.send_business_metric(
        metric_name='DailyActiveUsers',
        value=1250,
        dimensions={'Environment': 'dev'}
    )
    
    # System health check
    observability_client.send_business_metric(
        metric_name='HealthCheckStatus',
        value=1,  # 1 = healthy, 0 = unhealthy
        dimensions={
            'Environment': 'dev',
            'Service': 'ecommerce-api'
        }
    )
    
    print("Observability integration example completed!")