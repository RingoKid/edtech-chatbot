Hello AWS Trust & Safety,

Thank you for the prompt automated detection and for opening this case. Confirming that the account has been fully secured. All requested steps are complete. Detailed response below.

## Incident summary

On 2026-04-10 at 22:53:54 UTC, an unauthorized third party gained access to account 522534289122 via a leaked IAM access key (AKIAXTKLYP3RNHEBXQ5G, created 2025-09-17, belonging to the bdi-dev IAM user). CloudTrail Event History confirms a successful ConsoleLogin for bdi-dev at 2026-04-10 22:52:40 EDT — 74 seconds before the attacker minted a persistence access key — indicating the leaked credential bundle contained BOTH the access key and the console password.

We detected the compromise at approximately 23:25 EDT when the account owner (Yoon Jae Lee) forwarded an unexpected AWS SES DKIM verification notification for an unknown domain, bajisitan.pk. Full containment was achieved by 00:40 EDT on 2026-04-11.

The attacker TTPs match documented TruffleNet / Wiz SES-abuse campaign patterns: leaked long-lived IAM credentials → ~30-min automated dwell → 2-tier IAM persistence (admin user + region-scoped SES workers) → CreateEmailIdentity → AWS SES production-access auto-approval exploit under MailType=MARKETING → domain verified for outbound spam. During the 35-minute active exploitation window the attacker also filed 3 AWS Support cases from this account (177587733500135, 177587746600653, 177587778300402), all attacker-initiated.

## Confirmation of AWS's requested steps

**Step 1 (Change root password):** Completed by the account owner, Yoon Jae Lee. Password is new, unique, and not reused from any other service.

**Step 2 (Enable MFA on root):** Already enabled prior to this incident (virtual MFA device `arn:aws:iam::522534289122:mfa/Yoon`, enabled 2025-09-15). Confirmed still active.

**Step 3 (CloudTrail review and IAM cleanup):** Completed. Full audit of unauthorized IAM changes identified and deleted:

- `aws_user_1775878141` (AdministratorAccess): user + login profile deleted
- `aws_user_269306405` (AdministratorAccess): user + login profile + 1 access key (AKIAXTKLYP3RKOYPI6V2) deleted
- `ses_user_us-east-1_50286` (AmazonSESFullAccess + AmazonSESReadOnlyAccess): user + login profile deleted
- `ses_user_us-east-1_559910` (same): user + login profile deleted
- `ses_user_us-east-2_718366` (same): user + login profile deleted
- `ses_user_us-east-2_77870` (same): user + login profile deleted

Additional actions on the compromised `bdi-dev` IAM user:

- Both compromised access keys deleted: `AKIAXTKLYP3RNHEBXQ5G` (originally leaked) and `AKIAXTKLYP3RAM4SHFGR` (attacker-created persistence key)
- `bdi-dev` rotated to a fresh long-term access key
- `bdi-dev` console login profile deleted — user is now API-only
- Inline deny policy `AWSRevokeOlderSessions` attached to `bdi-dev` with a `DateLessThan` condition on `aws:TokenIssueTime` set to `2026-04-11T14:03:00Z`, invalidating any session credentials issued before that timestamp

Additional verification:

- No IAM roles were created or had trust policies modified by the attacker (audited all existing roles; only `AWSServiceRoleForServiceQuotas` is new — auto-created by AWS when the attacker called ServiceQuotas during recon)
- No inline user policies, SAML providers, or Federated users added
- No outstanding temporary security credentials
- Account password policy unchanged

Temporary incident-responder user: A temporary IAM user named `incident-responder` with `AdministratorAccess` was created by the root user during the incident response specifically to perform cleanup without using the compromised `bdi-dev` principal. This user will be deleted after this case is resolved and service access is restored.

**SES-specific cleanup:**

- SES identities `bajisitan.pk` and `no-reply@bajisitan.pk` deleted in both us-east-1 and us-east-2
- `sesv2 put-account-sending-attributes --no-sending-enabled` applied to both regions — account-level sending disabled
- `list-identities` returns empty in both regions, `SendingEnabled=false` confirmed

**Step 4 (Review for unwanted AWS usage):** Completed. All active regions (us-east-1, us-east-2, us-west-1, us-west-2, eu-west-1, eu-central-1, ap-south-1, ap-southeast-1, ap-northeast-1) swept for EC2, Lambda, S3, IAM roles, KMS, Secrets Manager, SSM, SNS, SQS, CloudFormation, EventBridge, Route53, CloudWatch alarms, App Runner, DynamoDB, ECR, and Amplify. All services clean — no attacker-created resources or modifications beyond the IAM users and SES identities listed above.

Billing impact: 2 test emails sent via the `bajisitan.pk` SES identity, estimated cost under $0.01.

## Requests

1. Please revoke the SES production access grants on cases `177587733500135` (us-east-1) and `177587778300402` (us-east-2). Both were filed by the attacker and auto-approved within minutes under MailType=MARKETING. Both are currently in "Reopened" status — please confirm revocation and return the account to SES sandbox mode in both regions.

2. Please close SES quota-increase case `177587746600653` as attacker-filed and fraudulent.

3. Please confirm when the temporary service limitation on the account is lifted.

4. Billing adjustment for the ~$0.01 of attacker SES usage.

5. The IAM naming pattern used by this attacker (`aws_user_<digits>` + `ses_user_<region>_<digits>`) does not appear in any public incident-response write-up we identified and may be a novel IOC worth correlating across other customer accounts being hit by the same automated TruffleNet-family campaign. Please consider forwarding to AWS Trust & Safety threat intelligence.

We are available for any additional information, CloudTrail exports, or forensic artifacts upon request.

**Primary contact:** Yoon Jae Lee (account owner, yoonlee@gsu.edu)
**Technical contact:** Naimul Islam (rifat.naimul@gmail.com)

Best regards,
Yoon Jae Lee / Naimul Islam
Account 522534289122
