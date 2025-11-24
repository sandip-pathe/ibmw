# GitHub App Setup Guide

This guide walks you through creating a GitHub App for the Fintech Compliance Engine.

## Step 1: Create GitHub App

1. Go to your GitHub account settings:
   - Personal account: `https://github.com/settings/apps`
   - Organization: `https://github.com/organizations/{org}/settings/apps`

2. Click **"New GitHub App"**

## Step 2: Basic Information

- **GitHub App name**: `Fintech Compliance Engine` (or your preferred name)
- **Homepage URL**: `https://your-domain.com` or `http://localhost:8000` for testing
- **Webhook URL**: `https://your-domain.com/webhook`
  - For local testing, use [ngrok](https://ngrok.com/): `ngrok http 8000`
  - Then use the ngrok URL: `https://abc123.ngrok.io/webhook`

- **Webhook secret**: Generate a strong secret:
mv ~/Downloads/your-app-name.2024-11-23.private-key.pem ./github-app-key.pem
chmod 600 ./github-app-key.pem

text
5. Set path in `.env`:
GITHUB_PRIVATE_KEY_PATH=./github-app-key.pem

text

## Step 6: Install the App

1. Go to app settings → **"Install App"**
2. Select the account/organization
3. Choose repositories:
- All repositories, or
- Only select repositories (recommended for testing)
4. Click **"Install"**

## Step 7: Verify Installation

1. Start your application:
./scripts/start-dev.sh
docker-compose up

text

2. Check logs for webhook events:
docker-compose logs -f api

text

3. You should see an `installation` webhook event

## Step 8: Test with a Push

1. Make a commit to an installed repository:
echo "# Test" >> README.md
git add README.md
git commit -m "Test compliance engine"
git push

text

2. Check application logs for `push` event
3. Verify indexing job was enqueued:
docker-compose logs -f worker

text

## Troubleshooting

### Webhook signature verification fails

- Ensure `GITHUB_WEBHOOK_SECRET` in `.env` matches GitHub App settings
- Check that webhook payload is sent as raw bytes (not pre-parsed JSON)

### Private key errors

- Verify file path in `GITHUB_PRIVATE_KEY_PATH` is correct
- Check file permissions: `chmod 600 github-app-key.pem`
- Ensure the key file is in PEM format (starts with `-----BEGIN RSA PRIVATE KEY-----`)

### Webhooks not received

- If testing locally, ensure ngrok is running: `ngrok http 8000`
- Update GitHub App webhook URL with current ngrok URL
- Check webhook deliveries in GitHub App settings → Recent Deliveries

### Installation token errors

- Verify `GITHUB_APP_ID` matches your app
- Check that private key is valid and matches the app
- Ensure app has required permissions

## Environment Variables Summary

Add these to your `.env` file:

GitHub App
GITHUB_APP_ID=123456
GITHUB_PRIVATE_KEY_PATH=./github-app-key.pem
GITHUB_WEBHOOK_SECRET=your-webhook-secret-here

text

## Security Best Practices

1. **Never commit** `github-app-key.pem` or `.env` to version control
2. Rotate webhook secret periodically
3. Regenerate private key if compromised
4. Use separate GitHub Apps for dev/staging/production
5. Limit app permissions to minimum required
6. Monitor webhook delivery failures and errors

## Next Steps

- Test code indexing by pushing to a repository
- Upload regulation data via `/admin/regulations/upload`
- Run compliance scans via `/analyze/repo/{repo_id}/scan`
- Monitor job queue: check Redis for job status

## References

- [GitHub Apps Documentation](https://docs.github.com/en/developers/apps)
- [Webhook Events](https://docs.github.com/en/developers/webhooks-and-events/webhooks/webhook-events-and-payloads)
- [Check Runs API](https://docs.github.com/en/rest/checks/runs)