"""
Environment-specific configuration management
"""
import os
from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

class Environment(Enum):
    DEV = "dev"
    STAGING = "staging"
    PROD = "prod"

@dataclass
class AlertingConfig:
    """Configuration for alerting thresholds and settings"""
    cpu_threshold: float
    error_rate_threshold: float
    duration_threshold_ms: float
    evaluation_periods: int
    datapoints_to_alarm: int

@dataclass
class LoggingConfig:
    """Configuration for logging settings"""
    retention_days: int
    log_level: str
    structured_logging: bool

@dataclass
class CostConfig:
    """Configuration for cost monitoring"""
    monthly_budget_limit: float
    anomaly_threshold_percent: float
    optimization_enabled: bool

@dataclass
class EnvironmentConfig:
    """Complete environment configuration"""
    environment: Environment
    alerting: AlertingConfig
    logging: LoggingConfig
    cost: CostConfig
    tags: Dict[str, str]

class ConfigManager:
    """Manages environment-specific configurations"""
    
    _configs = {
        Environment.DEV: EnvironmentConfig(
            environment=Environment.DEV,
            alerting=AlertingConfig(
                cpu_threshold=85.0,
                error_rate_threshold=10.0,
                duration_threshold_ms=15000,
                evaluation_periods=2,
                datapoints_to_alarm=2
            ),
            logging=LoggingConfig(
                retention_days=30,
                log_level="INFO",
                structured_logging=True
            ),
            cost=CostConfig(
                monthly_budget_limit=100.0,
                anomaly_threshold_percent=50.0,
                optimization_enabled=True
            ),
            tags={
                "Environment": "dev",
                "Project": "observability-platform",
                "Owner": "platform-team",
                "CostCenter": "engineering"
            }
        ),
        Environment.STAGING: EnvironmentConfig(
            environment=Environment.STAGING,
            alerting=AlertingConfig(
                cpu_threshold=80.0,
                error_rate_threshold=5.0,
                duration_threshold_ms=12000,
                evaluation_periods=3,
                datapoints_to_alarm=2
            ),
            logging=LoggingConfig(
                retention_days=90,
                log_level="INFO",
                structured_logging=True
            ),
            cost=CostConfig(
                monthly_budget_limit=500.0,
                anomaly_threshold_percent=30.0,
                optimization_enabled=True
            ),
            tags={
                "Environment": "staging",
                "Project": "observability-platform",
                "Owner": "platform-team",
                "CostCenter": "engineering"
            }
        ),
        Environment.PROD: EnvironmentConfig(
            environment=Environment.PROD,
            alerting=AlertingConfig(
                cpu_threshold=75.0,
                error_rate_threshold=1.0,
                duration_threshold_ms=10000,
                evaluation_periods=3,
                datapoints_to_alarm=3
            ),
            logging=LoggingConfig(
                retention_days=365,
                log_level="WARN",
                structured_logging=True
            ),
            cost=CostConfig(
                monthly_budget_limit=2000.0,
                anomaly_threshold_percent=20.0,
                optimization_enabled=True
            ),
            tags={
                "Environment": "prod",
                "Project": "observability-platform",
                "Owner": "platform-team",
                "CostCenter": "engineering",
                "Compliance": "required"
            }
        )
    }
    
    @classmethod
    def get_config(cls, environment: str) -> EnvironmentConfig:
        """Get configuration for specified environment"""
        env = Environment(environment.lower())
        return cls._configs[env]
    
    @classmethod
    def get_current_config(cls) -> EnvironmentConfig:
        """Get configuration for current environment from environment variable"""
        env_name = os.environ.get('ENVIRONMENT', 'dev')
        return cls.get_config(env_name)
    
    @classmethod
    def validate_config(cls, config: EnvironmentConfig) -> bool:
        """Validate configuration values"""
        return True  # Simplified for now