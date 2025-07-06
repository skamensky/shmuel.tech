# DNS Proxy Service

A secure proxy service for Namecheap DNS management API calls, supporting both production and sandbox environments with per-request configuration.

## Features

- ✅ Secure proxy authentication
- ✅ **Per-request** production and sandbox environment support
- ✅ Namecheap DNS record management (getHosts, setHosts)
- ✅ Docker containerization
- ✅ Health monitoring endpoints
- ✅ Modern web interface with multi-environment indicators

## Configuration

The service is configured using environment variables:

### Required Variables

- `PROXY_AUTH_TOKEN` - Authentication token for proxy access. Generate a secure random token for production use.

### Optional Variables

- `SERVICE_NAME` - Service name (default: `dns-proxy`)
- `PORT` - Port number (default: `80`)

### Environment Configuration

Unlike traditional approaches, this service uses **per-request environment selection**. Each API request can specify whether to use production or sandbox mode via the `sandbox` boolean field in the request payload.

```bash
# Single configuration for both environments
PROXY_AUTH_TOKEN=your-secure-token
SERVICE_NAME=dns-proxy
PORT=80
```

## Namecheap Sandbox Setup

When using sandbox mode (per request), you need:

1. **Separate Sandbox Account**: Create an account at https://sandbox.namecheap.com
2. **Separate API Credentials**: Enable API access in sandbox with different credentials
3. **Different Domains**: Register test domains in the sandbox environment
4. **IP Whitelisting**: Whitelist your IP address in the sandbox environment

### API Endpoints

The service automatically routes requests to the appropriate endpoint based on the `sandbox` field:

- **Production**: `https://api.namecheap.com/xml.response` (when `sandbox: false`)
- **Sandbox**: `https://api.sandbox.namecheap.com/xml.response` (when `sandbox: true`)

## Usage

### Running Locally

```bash
# Development mode
make dev

# Build and run with Docker
make build
make run
```

### Testing

```bash
# Run tests
make test
```

### Deployment

```bash
# Deploy to Fly.io
make deploy
```

### API Usage

The service provides a proxy endpoint at `/api/dns` that accepts POST requests with the following structure:

#### Production Request Example
```json
{
  "api_user": "your-namecheap-username",
  "api_key": "your-namecheap-api-key", 
  "client_ip": "your-whitelisted-ip",
  "command": "namecheap.domains.dns.getHosts",
  "data": {
    "domain": "example.com"
  },
  "proxy_auth": "your-proxy-auth-token",
  "sandbox": false
}
```

#### Sandbox Request Example
```json
{
  "api_user": "your-sandbox-username",
  "api_key": "your-sandbox-api-key", 
  "client_ip": "your-whitelisted-ip",
  "command": "namecheap.domains.dns.getHosts",
  "data": {
    "domain": "testdomain.com"
  },
  "proxy_auth": "your-proxy-auth-token",
  "sandbox": true
}
```

### Supported Commands

- `namecheap.domains.dns.getHosts` - Retrieve DNS records for a domain
- `namecheap.domains.dns.setHosts` - Update DNS records for a domain

### Health Check

The service provides a health check endpoint at `/health` that returns:

```json
{
  "status": "healthy",
  "service": "dns-proxy",
  "timestamp": "2024-01-01T00:00:00Z",
  "uptime": "1h23m45s",
  "supported_environments": ["production", "sandbox"]
}
```

### Web Interface

Access the web interface at the root URL (`/`) to view:

- Service status and information
- Multi-environment support indicator
- Per-request configuration details
- Health check link
- Security notices

## Security Features

- **Constant-time authentication** - Prevents timing attacks
- **IP whitelisting** - Namecheap API requires whitelisted IPs
- **Silent failure** - Invalid authentication attempts are silently dropped
- **HTTPS enforcement** - All API calls use HTTPS
- **Token-based access** - Secure proxy authentication
- **Per-request routing** - Environment isolation per request

## Development

### Building

```bash
# Build Docker image
docker build -t dns-proxy .

# Run locally
docker run --rm -p 8080:80 \
  -e PROXY_AUTH_TOKEN=test-token \
  dns-proxy
```

### Environment Variables for Development

```bash
# .env file example
PROXY_AUTH_TOKEN=development-test-token-123
SERVICE_NAME=dns-proxy-dev
PORT=8080
```

## Advantages of Per-Request Configuration

1. **Flexibility**: Single proxy server handles both environments
2. **Simplified Deployment**: No need for separate sandbox/production deployments
3. **Easy Testing**: Switch between environments without server restart
4. **Environment Isolation**: Each request is routed independently
5. **Cost Effective**: Single service instance instead of multiple

## Troubleshooting

### Common Issues

1. **Authentication Errors**: Verify your Namecheap API credentials and IP whitelisting for the respective environment
2. **Environment Mismatch**: Ensure you're using the correct credentials for your chosen environment (`sandbox: true/false`)
3. **Domain Not Found**: In sandbox mode, domains must be registered in the sandbox environment
4. **API Rate Limits**: Namecheap has rate limits (50/min, 700/hour, 8000/day) per environment

### Checking Configuration

Visit the `/health` endpoint to verify:
- Service status
- Supported environments (production, sandbox)
- Service uptime

### Request Examples

```bash
# Production request
curl -X POST http://localhost:8080/api/dns \
  -H "Content-Type: application/json" \
  -d '{
    "api_user": "production-user",
    "api_key": "production-key",
    "client_ip": "1.2.3.4",
    "command": "namecheap.domains.dns.getHosts",
    "data": {"domain": "example.com"},
    "proxy_auth": "your-token",
    "sandbox": false
  }'

# Sandbox request
curl -X POST http://localhost:8080/api/dns \
  -H "Content-Type: application/json" \
  -d '{
    "api_user": "sandbox-user",
    "api_key": "sandbox-key",
    "client_ip": "1.2.3.4",
    "command": "namecheap.domains.dns.getHosts",
    "data": {"domain": "testdomain.com"},
    "proxy_auth": "your-token",
    "sandbox": true
  }'
```

## License

This project is licensed under the MIT License. 