# Domain Setup

Custom domain configuration for `composeearly.com` using AWS Route 53 and Amplify.

## Architecture

```
                                    ┌─────────────────────────────────────────┐
                                    │              AWS Cloud                  │
                                    │                                         │
┌──────────┐    DNS Query           │  ┌─────────────┐      ┌─────────────┐  │
│  User    │ ───────────────────────┼─▶│  Route 53   │─────▶│ CloudFront  │  │
│ Browser  │                        │  │   (DNS)     │      │   (CDN)     │  │
└──────────┘                        │  └─────────────┘      └──────┬──────┘  │
     │                              │                              │         │
     │         HTTPS Response       │                              ▼         │
     └◀─────────────────────────────┼───────────────────────┌─────────────┐  │
                                    │                       │   Amplify   │  │
                                    │                       │  (Hosting)  │  │
                                    │                       └─────────────┘  │
                                    │                                         │
                                    └─────────────────────────────────────────┘
```

**Flow:**
1. User visits `composeearly.com` or `www.composeearly.com`
2. Route 53 resolves domain to CloudFront distribution
3. CloudFront serves cached content or forwards to Amplify
4. Amplify returns the app (from `develop` branch)

## AWS Resources

| Resource | ID / Value | Description |
|----------|------------|-------------|
| **Route 53 Hosted Zone** | `Z0759078VHUWMF02PNU4` | DNS zone for composeearly.com |
| **Amplify App** | `dyio3npn4doy2` | edtech-chatbot-fe |
| **Amplify Default Domain** | `dyio3npn4doy2.amplifyapp.com` | Fallback URL |
| **CloudFront Distribution** | `d20h66hq0frc0f.cloudfront.net` | CDN endpoint |
| **Active Branch** | `develop` | Branch deployed to custom domain |
| **Region** | `us-east-1` | All resources |

## DNS Configuration

Current records in Route 53 hosted zone:

| Name | Type | Value | Purpose |
|------|------|-------|---------|
| `composeearly.com` | A (ALIAS) | `d20h66hq0frc0f.cloudfront.net` | Root domain to CloudFront |
| `www.composeearly.com` | CNAME | `d20h66hq0frc0f.cloudfront.net` | www subdomain to CloudFront |
| `composeearly.com` | NS | `ns-1478.awsdns-56.org`, `ns-816.awsdns-38.net`, `ns-165.awsdns-20.com`, `ns-1906.awsdns-46.co.uk` | Nameservers |

## Common Operations

### Check Domain Status

```bash
aws amplify get-domain-association \
  --app-id dyio3npn4doy2 \
  --domain-name composeearly.com \
  --region us-east-1
```

### List All DNS Records

```bash
aws route53 list-resource-record-sets \
  --hosted-zone-id Z0759078VHUWMF02PNU4
```

### Add a New Subdomain

Example: Adding `api.composeearly.com` pointing to App Runner

```bash
aws route53 change-resource-record-sets \
  --hosted-zone-id Z0759078VHUWMF02PNU4 \
  --change-batch '{
    "Changes": [{
      "Action": "UPSERT",
      "ResourceRecordSet": {
        "Name": "api.composeearly.com",
        "Type": "CNAME",
        "TTL": 300,
        "ResourceRecords": [{"Value": "your-apprunner-url.awsapprunner.com"}]
      }
    }]
  }'
```

### Change Branch for Domain

```bash
aws amplify update-domain-association \
  --app-id dyio3npn4doy2 \
  --domain-name composeearly.com \
  --sub-domain-settings '[
    {"prefix": "", "branchName": "main"},
    {"prefix": "www", "branchName": "main"}
  ]' \
  --region us-east-1
```

### Verify DNS Propagation

```bash
# Check if domain resolves correctly
dig composeearly.com A +short
dig www.composeearly.com CNAME +short

# Check from multiple locations
# https://www.whatsmydns.net/#A/composeearly.com
```

### Setup Email (MX Records)

Example for Google Workspace:

```bash
aws route53 change-resource-record-sets \
  --hosted-zone-id Z0759078VHUWMF02PNU4 \
  --change-batch '{
    "Changes": [{
      "Action": "UPSERT",
      "ResourceRecordSet": {
        "Name": "composeearly.com",
        "Type": "MX",
        "TTL": 300,
        "ResourceRecords": [
          {"Value": "1 aspmx.l.google.com"},
          {"Value": "5 alt1.aspmx.l.google.com"},
          {"Value": "5 alt2.aspmx.l.google.com"}
        ]
      }
    }]
  }'
```

## Domain Registration

| Field | Value |
|-------|-------|
| **Registrar** | AWS Route 53 |
| **Registered Name** | ComposeEarly |
| **Admin Email** | rifat.naimul@gmail.com |
| **Auto-Renew** | Enabled |
| **Privacy Protection** | Enabled |

Check registration details:
```bash
aws route53domains get-domain-detail \
  --domain-name composeearly.com \
  --region us-east-1
```

## Lessons Learned

### Root Domain CNAME Limitation

**Problem:** We initially tried to point `composeearly.com` from Wix DNS to Amplify, but it didn't work.

**Why:**
- Root domains (apex domains like `composeearly.com`) cannot use CNAME records per DNS specification
- CNAME records are only valid for subdomains (like `www.composeearly.com`)
- The root must have SOA and NS records, which conflict with CNAME

**Solutions:**
| Solution | How it works |
|----------|--------------|
| **ALIAS record (Route 53)** | AWS-proprietary record type that acts like CNAME but is allowed at apex |
| **CNAME flattening (Cloudflare)** | Resolves CNAME to IP at query time, returns as A record |
| **ANAME record** | Similar to ALIAS, supported by some DNS providers |

**Why Wix didn't work:** Wix DNS doesn't support ALIAS, ANAME, or CNAME flattening. Only Route 53 (or similar providers like Cloudflare) can properly point a root domain to CloudFront/Amplify.

### Transfer vs Nameserver Change

Two ways to move DNS away from a registrar:

| Method | What moves | Time | Use when |
|--------|------------|------|----------|
| **Nameserver change** | Only DNS management | Minutes | You want to keep registration at original provider |
| **Domain transfer** | Registration + DNS | 5-7 days | You want everything in one place |

We did a full transfer because:
1. Simpler long-term management (everything in AWS)
2. Needed ALIAS record support (Route 53)
3. Avoids split-brain scenarios between registrar and DNS provider

### Domain Transfer Doesn't Update Nameservers Automatically

**Problem:** After the domain transfer completed, the site was still showing the old Wix website.

**Why:** Domain transfer moves the *registration* to AWS, but doesn't automatically update the *nameservers*. The domain was still pointing to Wix's nameservers (`ns6.wixdns.net`), which no longer had our DNS records.

**Fix:**
```bash
aws route53domains update-domain-nameservers \
  --domain-name composeearly.com \
  --nameservers \
    Name=ns-1478.awsdns-56.org \
    Name=ns-816.awsdns-38.net \
    Name=ns-165.awsdns-20.com \
    Name=ns-1906.awsdns-46.co.uk \
  --region us-east-1
```

**Verification:**
```bash
# Check which nameservers are active (may take 15 min - 48 hrs to propagate)
dig composeearly.com NS +short

# Should show awsdns nameservers, NOT wixdns
```

**Lesson:** After a domain transfer, always verify nameservers are pointing to your new DNS provider's nameservers, not the old ones.
