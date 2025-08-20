#!/usr/bin/env python3
import aws_cdk as cdk
from observability.stacks.core_stack import CoreObservabilityStack
from observability.stacks.dashboard_stack import DashboardStack
from observability.stacks.alerting_stack import AlertingStack
from observability.stacks.automation_stack import AutomationStack
from observability.stacks.cost_monitoring_stack import CostMonitoringStack
from observability.stacks.log_analysis_stack import LogAnalysisStack

app = cdk.App()

# Get environment configuration
env_name = app.node.try_get_context("environment") or "dev"
account = app.node.try_get_context("account")
region = app.node.try_get_context("region") or "us-east-1"

env = cdk.Environment(account=account, region=region)

# Core observability infrastructure
core_stack = CoreObservabilityStack(
    app, f"ObservabilityCore-{env_name}",
    env=env,
    environment=env_name
)

# Dashboards for monitoring
dashboard_stack = DashboardStack(
    app, f"ObservabilityDashboards-{env_name}",
    env=env,
    environment=env_name,
    core_resources=core_stack.core_resources
)

# Alerting and notifications
alerting_stack = AlertingStack(
    app, f"ObservabilityAlerting-{env_name}",
    env=env,
    environment=env_name,
    core_resources=core_stack.core_resources
)

# Automation and remediation
automation_stack = AutomationStack(
    app, f"ObservabilityAutomation-{env_name}",
    env=env,
    environment=env_name,
    core_resources=core_stack.core_resources,
    alerting_resources=alerting_stack.alerting_resources
)

# Cost monitoring
cost_stack = CostMonitoringStack(
    app, f"ObservabilityCost-{env_name}",
    env=env,
    environment=env_name,
    core_resources=core_stack.core_resources
)

# Log analysis
log_stack = LogAnalysisStack(
    app, f"ObservabilityLogs-{env_name}",
    env=env,
    environment=env_name,
    core_resources=core_stack.core_resources
)

app.synth()