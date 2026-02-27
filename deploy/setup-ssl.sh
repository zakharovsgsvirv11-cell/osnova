#!/usr/bin/env bash
# Setup SSL certificate via Let's Encrypt (certbot)
# Usage: sudo ./setup-ssl.sh mcp.example.com

set -euo pipefail

DOMAIN="${1:?Usage: $0 <domain>}"
EMAIL="${2:-}"

echo "=== Email-MCP SSL Setup ==="
echo "Domain: ${DOMAIN}"

# Install certbot if needed
if ! command -v certbot &>/dev/null; then
    echo "Installing certbot..."
    if command -v apt-get &>/dev/null; then
        apt-get update && apt-get install -y certbot python3-certbot-nginx
    elif command -v dnf &>/dev/null; then
        dnf install -y certbot python3-certbot-nginx
    else
        echo "ERROR: Install certbot manually for your OS."
        exit 1
    fi
fi

# Create webroot for challenges
mkdir -p /var/www/certbot

# Obtain certificate
CERTBOT_ARGS=(
    certonly
    --nginx
    -d "${DOMAIN}"
    --non-interactive
    --agree-tos
)

if [ -n "${EMAIL}" ]; then
    CERTBOT_ARGS+=(--email "${EMAIL}")
else
    CERTBOT_ARGS+=(--register-unsafely-without-email)
fi

certbot "${CERTBOT_ARGS[@]}"

# Setup auto-renewal cron (if not already configured)
if ! crontab -l 2>/dev/null | grep -q certbot; then
    (crontab -l 2>/dev/null; echo "0 3 * * * certbot renew --quiet --post-hook 'systemctl reload nginx'") | crontab -
    echo "Auto-renewal cron job added (daily at 3 AM)."
fi

echo ""
echo "=== SSL certificate obtained ==="
echo "Certificate: /etc/letsencrypt/live/${DOMAIN}/fullchain.pem"
echo "Private key: /etc/letsencrypt/live/${DOMAIN}/privkey.pem"
echo ""
echo "Next steps:"
echo "1. Update deploy/nginx/email-mcp.conf: replace YOUR_DOMAIN with ${DOMAIN}"
echo "2. Copy nginx config:  sudo cp deploy/nginx/email-mcp.conf /etc/nginx/sites-enabled/"
echo "3. Test & reload:      sudo nginx -t && sudo systemctl reload nginx"
