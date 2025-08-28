# ADR-001: Architecture Decisions

## Status
Accepted

## Key Decisions

### CDK with Python
**Why**: Type safety, reusable constructs, native AWS integration

### EventBridge for Event Routing
**Why**: Decoupled architecture, easy external integrations, built-in retry

### Multi-Severity SNS Topics
**Why**: Prevents alert fatigue, flexible routing, easy to extend

### Step Functions for Remediation
**Why**: Visual workflows, error handling, audit trail

### KMS Encryption by Default
**Why**: Security best practices, compliance, key rotation

## Trade-offs

**Pros**: Scalable, secure, maintainable
**Cons**: More complex than basic CloudWatch setup, requires CDK knowledge

## Alternatives Considered
- **Terraform**: Rejected due to lack of type safety
- **CloudWatch Events**: Rejected as legacy, EventBridge is better
- **Lambda-only workflows**: Rejected, Step Functions provide better workflow management