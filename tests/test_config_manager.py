"""
Unit tests for configuration manager
"""
import unittest
import os
from src.config.environment_config import ConfigManager, Environment, EnvironmentConfig

class TestConfigManager(unittest.TestCase):
    """Test cases for ConfigManager class"""
    
    def test_get_config_dev(self):
        """Test getting dev configuration"""
        config = ConfigManager.get_config('dev')
        
        self.assertEqual(config.environment, Environment.DEV)
        self.assertEqual(config.alerting.cpu_threshold, 85.0)
        self.assertEqual(config.logging.retention_days, 30)
        self.assertEqual(config.cost.monthly_budget_limit, 100.0)
        self.assertIn('Environment', config.tags)
        self.assertEqual(config.tags['Environment'], 'dev')
    
    def test_get_config_staging(self):
        """Test getting staging configuration"""
        config = ConfigManager.get_config('staging')
        
        self.assertEqual(config.environment, Environment.STAGING)
        self.assertEqual(config.alerting.cpu_threshold, 80.0)
        self.assertEqual(config.logging.retention_days, 90)
        self.assertEqual(config.cost.monthly_budget_limit, 500.0)
        self.assertEqual(config.tags['Environment'], 'staging')
    
    def test_get_config_prod(self):
        """Test getting prod configuration"""
        config = ConfigManager.get_config('prod')
        
        self.assertEqual(config.environment, Environment.PROD)
        self.assertEqual(config.alerting.cpu_threshold, 75.0)
        self.assertEqual(config.logging.retention_days, 365)
        self.assertEqual(config.cost.monthly_budget_limit, 2000.0)
        self.assertEqual(config.tags['Environment'], 'prod')
        self.assertIn('Compliance', config.tags)
    
    def test_get_config_invalid(self):
        """Test getting configuration for invalid environment"""
        with self.assertRaises(ValueError):
            ConfigManager.get_config('invalid')
    
    def test_get_current_config_default(self):
        """Test getting current configuration with default"""
        # Ensure ENVIRONMENT is not set
        if 'ENVIRONMENT' in os.environ:
            del os.environ['ENVIRONMENT']
        
        config = ConfigManager.get_current_config()
        self.assertEqual(config.environment, Environment.DEV)
    
    def test_get_current_config_from_env(self):
        """Test getting current configuration from environment variable"""
        os.environ['ENVIRONMENT'] = 'prod'
        
        config = ConfigManager.get_current_config()
        self.assertEqual(config.environment, Environment.PROD)
        
        # Clean up
        del os.environ['ENVIRONMENT']
    
    def test_validate_config_valid(self):
        """Test validation of valid configuration"""
        config = ConfigManager.get_config('dev')
        is_valid = ConfigManager.validate_config(config)
        self.assertTrue(is_valid)
    
    def test_validate_config_invalid_cpu_threshold(self):
        """Test validation with invalid CPU threshold"""
        config = ConfigManager.get_config('dev')
        config.alerting.cpu_threshold = 150.0  # Invalid: > 100
        
        is_valid = ConfigManager.validate_config(config)
        self.assertFalse(is_valid)
        
        config.alerting.cpu_threshold = -10.0  # Invalid: < 0
        is_valid = ConfigManager.validate_config(config)
        self.assertFalse(is_valid)
    
    def test_validate_config_invalid_error_rate(self):
        """Test validation with invalid error rate"""
        config = ConfigManager.get_config('dev')
        config.alerting.error_rate_threshold = -5.0  # Invalid: < 0
        
        is_valid = ConfigManager.validate_config(config)
        self.assertFalse(is_valid)
    
    def test_validate_config_invalid_duration(self):
        """Test validation with invalid duration threshold"""
        config = ConfigManager.get_config('dev')
        config.alerting.duration_threshold_ms = -1000  # Invalid: <= 0
        
        is_valid = ConfigManager.validate_config(config)
        self.assertFalse(is_valid)
    
    def test_validate_config_invalid_retention(self):
        """Test validation with invalid log retention"""
        config = ConfigManager.get_config('dev')
        config.logging.retention_days = 0  # Invalid: <= 0
        
        is_valid = ConfigManager.validate_config(config)
        self.assertFalse(is_valid)
    
    def test_validate_config_invalid_log_level(self):
        """Test validation with invalid log level"""
        config = ConfigManager.get_config('dev')
        config.logging.log_level = 'INVALID'  # Invalid log level
        
        is_valid = ConfigManager.validate_config(config)
        self.assertFalse(is_valid)
    
    def test_validate_config_invalid_budget(self):
        """Test validation with invalid budget limit"""
        config = ConfigManager.get_config('dev')
        config.cost.monthly_budget_limit = -100.0  # Invalid: <= 0
        
        is_valid = ConfigManager.validate_config(config)
        self.assertFalse(is_valid)
    
    def test_validate_config_invalid_anomaly_threshold(self):
        """Test validation with invalid anomaly threshold"""
        config = ConfigManager.get_config('dev')
        config.cost.anomaly_threshold_percent = 150.0  # Invalid: > 100
        
        is_valid = ConfigManager.validate_config(config)
        self.assertFalse(is_valid)
        
        config.cost.anomaly_threshold_percent = -10.0  # Invalid: <= 0
        is_valid = ConfigManager.validate_config(config)
        self.assertFalse(is_valid)

if __name__ == '__main__':
    unittest.main()