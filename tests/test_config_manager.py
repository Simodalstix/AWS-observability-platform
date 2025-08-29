"""
Unit tests for configuration manager
"""
import unittest
import os
from src.config.environment_config import ConfigManager, Environment

class TestConfigManager(unittest.TestCase):
    """Test cases for ConfigManager class"""
    
    def test_get_config_dev(self):
        """Test getting dev configuration"""
        config = ConfigManager.get_config('dev')
        self.assertEqual(config.environment, Environment.DEV)
        self.assertEqual(config.tags['Environment'], 'dev')
    
    def test_get_config_staging(self):
        """Test getting staging configuration"""
        config = ConfigManager.get_config('staging')
        self.assertEqual(config.environment, Environment.STAGING)
        self.assertEqual(config.tags['Environment'], 'staging')
    
    def test_get_config_prod(self):
        """Test getting prod configuration"""
        config = ConfigManager.get_config('prod')
        self.assertEqual(config.environment, Environment.PROD)
        self.assertEqual(config.tags['Environment'], 'prod')
    
    def test_get_config_invalid(self):
        """Test getting configuration for invalid environment"""
        with self.assertRaises(ValueError):
            ConfigManager.get_config('invalid')
    
    def test_get_current_config_default(self):
        """Test getting current configuration with default"""
        if 'ENVIRONMENT' in os.environ:
            del os.environ['ENVIRONMENT']
        
        config = ConfigManager.get_current_config()
        self.assertEqual(config.environment, Environment.DEV)

if __name__ == '__main__':
    unittest.main()