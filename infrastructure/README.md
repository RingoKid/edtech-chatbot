# EdTech Chatbot Infrastructure

This directory contains AWS CDK (Cloud Development Kit) infrastructure code for the EdTech Chatbot application.

## Overview

The `EdTechChatbotInfraStack` creates:
- A DynamoDB table with environment-specific naming
- Partition key: `PK` (string)
- Sort key: `SK` (string)
- Global Secondary Index: `EmailIndex` with partition key `email`
- PAY_PER_REQUEST billing mode
- Auto-deletion when stack is destroyed (useful for sandbox environments)

## Environment-based Table Naming

The stack reads the `APP_ENV` environment variable and creates tables with the following naming pattern:
- `local`: `EdTechChatbotTable-local`
- `sandbox`: `EdTechChatbotTable-sandbox` (default)
- `production`: `EdTechChatbotTable-production`

## Setup Instructions

1. **Install dependencies:**
   ```bash
   cd infrastructure
   pip install -r requirements.txt
   ```

2. **Install AWS CDK CLI (if not already installed):**
   ```bash
   npm install -g aws-cdk
   ```

3. **Configure AWS credentials** (using AWS CLI or environment variables)

4. **Bootstrap CDK (one-time setup per AWS account/region):**
   ```bash
   cdk bootstrap
   ```

## Deployment

### Deploy to Sandbox (default):
```bash
cd infrastructure
cdk deploy
```

### Deploy to Production:
```bash
cd infrastructure
export APP_ENV=production
cdk deploy
```

### Deploy to Local:
```bash
cd infrastructure
export APP_ENV=local
cdk deploy
```

## Other CDK Commands

- **View differences:** `cdk diff`
- **Synthesize CloudFormation:** `cdk synth`
- **Destroy stack:** `cdk destroy`
- **List stacks:** `cdk ls`

## Stack Outputs

After deployment, the stack will output:
- `DynamoDBTableName`: The actual table name created
- `DynamoDBTableArn`: The ARN of the created table

These can be used by your application for configuration.
