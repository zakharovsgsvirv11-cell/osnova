#!/usr/bin/env bash
# Deploy email-mcp with HTTPS
# Usage: ./deploy/deploy.sh mcp.example.com [your@email.com]
set -euo pipefail

DOMAIN="${1:?Usage: $0 <domain> [email]}"
EMAIL="${2:-}"
PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

echo "=== Email-MCP Deployment ==="
echo "Domain: ${DOMAIN}"
echo "Project: ${PROJECT_DIR}"
echo ""

# ── 1. Validate .env ────────────────────────────────────────────
if [ ! -f "${PROJECT_DIR}/.env" ]; then
    echo "ERROR: .env not found. Copy and fill: cp .env.example .env"
    exit 1
fi

if grep -q "CHANGE_ME" "${PROJECT_DIR}/.env"; then
    echo "ERROR: MCP_API_KEY has placeholder value."
    echo "Generate a key: python3 -c \"import secrets; print(secrets.token_urlsafe(48))\""
    exit 1
fi

# ── 2. Patch nginx config with domain and API key ───────────────
API_KEY=$(grep "^MCP_API_KEY=" "${PROJECT_DIR}/.env" | cut -d= -f2-)
NGINX_CONF="${PROJECT_DIR}/deploy/nginx/email-mcp.conf"

sed -i "s/YOUR_DOMAIN/${DOMAIN}/g" "${NGINX_CONF}"
sed -i "s/YOUR_MCP_API_KEY/${API_KEY}/g" "${NGINX_CONF}"
echo "Nginx config patched with domain and API key."

# ── 3. Initial certificate (HTTP-only mode first) ──────────────
echo ""
echo "Step 1: Starting nginx in HTTP-only mode for certificate..."

# Temporarily use a simple HTTP config for certbot challenge
cat > /tmp/email-mcp-init.conf <<INITCONF
server {
    listen 80;
    server_name ${DOMAIN};
    location /.well-known/acme-challenge/ { root /var/www/certbot; }
    location / { return 200 'waiting for ssl'; }
}
INITCONF

# Run certbot standalone to get initial cert
docker compose -f "${PROJECT_DIR}/docker-compose.yml" run --rm \
    -v "${PROJECT_DIR}/deploy/nginx/email-mcp.conf:/etc/nginx/conf.d/default.conf:ro" \
    certbot certonly --webroot --webroot-path=/var/www/certbot \
    -d "${DOMAIN}" \
    --non-interactive --agree-tos \
    ${EMAIL:+--email "${EMAIL}"} \
    ${EMAIL:---register-unsafely-without-email} \
    || true

# ── 4. Start everything ────────────────────────────────────────
echo ""
echo "Step 2: Starting all services..."
docker compose -f "${PROJECT_DIR}/docker-compose.yml" up -d --build

echo ""
echo "=== Deployment complete ==="
echo "MCP endpoint: https://${DOMAIN}/sse"
echo ""
echo "Claude Desktop config (~/.claude/claude_desktop_config.json):"
echo "{"
echo "  \"mcpServers\": {"
echo "    \"email\": {"
echo "      \"url\": \"https://${DOMAIN}/sse\","
echo "      \"headers\": {"
echo "        \"Authorization\": \"Bearer ${API_KEY}\""
echo "      }"
echo "    }"
echo "  }"
echo "}"
