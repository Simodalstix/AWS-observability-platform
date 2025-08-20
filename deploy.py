#!/usr/bin/env python3
"""
Deployment script for AWS Observability Platform
"""
import subprocess
import sys
import json
import boto3
from typing import Dict, Any

def check_prerequisites():
    """Check if required tools are installed"""
    required_tools = ['aws', 'cdk']
    
    for tool in required_tools:
        try:
            subprocess.run([tool, '--version'], check=True, capture_output=True)
            print(f"[OK] {tool} is installed")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print(f"[ERROR] {tool} is not installed or not in PATH")
            return False
    
    return True

def get_aws_account_info():
    """Get AWS account and region information"""
    try:
        sts = boto3.client('sts')
        identity = sts.get_caller_identity()
        
        session = boto3.Session()
        region = session.region_name or 'us-east-1'
        
        return {
            'account': identity['Account'],
            'region': region
        }
    except Exception as e:
        print(f"Error getting AWS account info: {e}")
        return None

def bootstrap_cdk(account: str, region: str):
    """Bootstrap CDK in the target account/region"""
    print(f"Bootstrapping CDK in account {account}, region {region}...")
    
    try:
        subprocess.run([
            'cdk', 'bootstrap', 
            f'aws://{account}/{region}'
        ], check=True)
        print("[OK] CDK bootstrap completed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] CDK bootstrap failed: {e}")
        return False

def install_dependencies():
    """Install Python dependencies"""
    print("Installing Python dependencies...")
    
    try:
        subprocess.run([
            sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'
        ], check=True)
        print("[OK] Dependencies installed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Failed to install dependencies: {e}")
        return False

def deploy_stacks(environment: str, account: str, region: str):
    """Deploy CDK stacks"""
    print(f"Deploying observability platform for environment: {environment}")
    
    # Set context variables
    context_args = [
        '--context', f'environment={environment}',
        '--context', f'account={account}',
        '--context', f'region={region}'
    ]
    
    try:
        # Deploy all stacks
        subprocess.run([
            'cdk', 'deploy', '--all', '--require-approval', 'never'
        ] + context_args, check=True)
        
        print("[OK] All stacks deployed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Deployment failed: {e}")
        return False

def create_integration_guide():
    """Create integration guide for existing projects"""
    import shutil
    import os
    
    # Copy pre-existing integration guide template
    template_path = 'docs/INTEGRATION_GUIDE_TEMPLATE.md'
    if os.path.exists(template_path):
        shutil.copy(template_path, 'INTEGRATION_GUIDE.md')
        print("[OK] Integration guide created: INTEGRATION_GUIDE.md")
    else:
        print("[WARNING] Integration guide template not found, skipping creation")

def main():
    """Main deployment function"""
    print("AWS Observability Platform Deployment")
    print("=" * 50)
    
    # Check prerequisites
    if not check_prerequisites():
        print("Please install missing prerequisites and try again.")
        sys.exit(1)
    
    # Get AWS account info
    aws_info = get_aws_account_info()
    if not aws_info:
        print("Could not get AWS account information. Please check your AWS credentials.")
        sys.exit(1)
    
    print(f"Deploying to account: {aws_info['account']}")
    print(f"Region: {aws_info['region']}")
    
    # Get environment
    environment = input("Enter environment (dev/staging/prod) [dev]: ").strip() or "dev"
    
    # Install dependencies
    if not install_dependencies():
        sys.exit(1)
    
    # Bootstrap CDK
    if not bootstrap_cdk(aws_info['account'], aws_info['region']):
        sys.exit(1)
    
    # Deploy stacks
    if not deploy_stacks(environment, aws_info['account'], aws_info['region']):
        sys.exit(1)
    
    # Create integration guide
    create_integration_guide()
    
    print("\nDeployment completed successfully!")
    print("\nNext steps:")
    print("1. Review the INTEGRATION_GUIDE.md file")
    print("2. Configure email addresses for alerts in SNS topics")
    print("3. Set up Slack integration if needed")
    print("4. Review and customize dashboards")
    print("5. Test the monitoring with sample applications")

if __name__ == "__main__":
    main()