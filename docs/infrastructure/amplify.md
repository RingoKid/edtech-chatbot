# Amplify

Frontend hosting and CI/CD for the React application.

## Architecture

```
┌───────────────────────────────────────────────────────────────────┐
│                        Amplify Hosting                            │
│                                                                   │
│  ┌──────────┐     ┌───────────────┐     ┌─────────────────────┐  │
│  │  GitHub  │────▶│ Amplify Build │────▶│  CloudFront CDN     │  │
│  │  Push    │     │  (npm build)  │     │                     │  │
│  └──────────┘     └───────────────┘     │  composeearly.com   │  │
│                                         │  *.amplifyapp.com   │  │
│                                         └─────────────────────┘  │
└───────────────────────────────────────────────────────────────────┘
```

## AWS Resources

| Property | Value |
|----------|-------|
| **App Name** | `edtech-chatbot-fe` |
| **App ID** | `dyio3npn4doy2` |
| **Default Domain** | `dyio3npn4doy2.amplifyapp.com` |
| **Custom Domain** | `composeearly.com` |
| **Repository** | `https://github.com/RingoKid/edtech-chatbot` |
| **Region** | `us-east-1` |
| **Created** | 2025-09-28 |

## Branch Configuration

| Branch | Stage | URL | Auto-Build |
|--------|-------|-----|------------|
| `develop` | DEVELOPMENT | `develop.dyio3npn4doy2.amplifyapp.com` | Enabled |

### Environment Variables (develop branch)

| Variable | Value |
|----------|-------|
| `VITE_API_BASE_URL` | `https://mkbifgscip.us-east-1.awsapprunner.com/api/v1` |

## Build Configuration

From `amplify.yml`:

```yaml
version: 1
frontend:
  phases:
    preBuild:
      commands:
        - cd frontend
        - npm ci
    build:
      commands:
        - npm run build
  artifacts:
    baseDirectory: frontend/dist
    files:
      - '**/*'
  cache:
    paths:
      - frontend/node_modules/**/*
```

### Build Compute

| Property | Value |
|----------|-------|
| **Compute Type** | STANDARD_8GB |
| **Cache** | AMPLIFY_MANAGED_NO_COOKIES |

## Custom Headers (Security)

Applied to all files (`**/*`):

| Header | Value | Purpose |
|--------|-------|---------|
| `X-Frame-Options` | `DENY` | Prevent clickjacking |
| `X-XSS-Protection` | `1; mode=block` | XSS filter |
| `X-Content-Type-Options` | `nosniff` | Prevent MIME sniffing |

## Redirect Rules

| Source | Target | Status | Purpose |
|--------|--------|--------|---------|
| `https://www.composeearly.com` | `https://composeearly.com` | 301 | www → bare domain redirect |
| `https://www.composeearly.com/<*>` | `https://composeearly.com/<*>` | 301 | www → bare domain (all paths) |
| `/<*>` | `/index.html` | 404-200 | SPA routing (React Router) |

The www redirects prevent CORS errors — without them, `www.composeearly.com` is a different origin than `composeearly.com`, and the backend would reject the request. The SPA rule ensures client-side routing works.

## Common Operations

### Check App Status

```bash
aws amplify get-app --app-id dyio3npn4doy2 --region us-east-1
```

### List Branches

```bash
aws amplify list-branches --app-id dyio3npn4doy2 --region us-east-1
```

### Get Branch Details

```bash
aws amplify get-branch \
  --app-id dyio3npn4doy2 \
  --branch-name develop \
  --region us-east-1
```

### List Recent Builds

```bash
aws amplify list-jobs \
  --app-id dyio3npn4doy2 \
  --branch-name develop \
  --region us-east-1
```

### Trigger Manual Build

```bash
aws amplify start-job \
  --app-id dyio3npn4doy2 \
  --branch-name develop \
  --job-type RELEASE \
  --region us-east-1
```

### Update Environment Variable

```bash
aws amplify update-branch \
  --app-id dyio3npn4doy2 \
  --branch-name develop \
  --environment-variables "VITE_API_BASE_URL=https://new-url.com/api/v1" \
  --region us-east-1
```

### Add New Branch

```bash
aws amplify create-branch \
  --app-id dyio3npn4doy2 \
  --branch-name main \
  --stage PRODUCTION \
  --enable-auto-build \
  --region us-east-1
```

### Check Domain Status

```bash
aws amplify get-domain-association \
  --app-id dyio3npn4doy2 \
  --domain-name composeearly.com \
  --region us-east-1
```

## Code References

| File | Purpose |
|------|---------|
| `amplify.yml` | Build and deploy configuration |
| `frontend/` | React application source |
| `frontend/vite.config.ts` | Vite build configuration |

## Deployment Pipeline

1. **Push to `develop` branch** on GitHub
2. **Amplify webhook** triggers build
3. **Build phases**:
   - `preBuild`: `cd frontend && npm ci`
   - `build`: `npm run build`
4. **Artifacts** from `frontend/dist/` deployed to CDN
5. **Invalidation** clears CloudFront cache
6. Available at branch URL and custom domain

## Troubleshooting

### Build failing on npm ci

Check `package-lock.json` is committed and matches `package.json`:
```bash
cd frontend && npm ci
```

### Environment variables not updating

After changing env vars, trigger a new build:
```bash
aws amplify start-job \
  --app-id dyio3npn4doy2 \
  --branch-name develop \
  --job-type RELEASE \
  --region us-east-1
```

### 404 on page refresh

Ensure redirect rule exists:
- Source: `/<*>`
- Target: `/index.html`
- Status: `404-200`

### Custom domain not working

See `domain-setup.md` for Route 53 and CloudFront configuration.

## Related Docs

- `domain-setup.md` — Route 53 DNS and custom domain configuration
- `app-runner.md` — Backend API that frontend connects to
