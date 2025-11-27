# jscom-api

Python client and CLI for johnsosoka.com API services.

## Installation

```bash
poetry add jscom-api
```

For development:

```bash
git clone <repository>
cd jscom-api-client
poetry install
```

## CLI Usage

### Get Your Public IP

```bash
# Human-readable table output
jscom-api ip

# JSON output
jscom-api ip --json

# Plain IP only
jscom-api ip --quiet
```

### Update DNS Record

```bash
# Update with specific IP
jscom-api dns update --domain mc.example.com. --ip 1.2.3.4

# Auto-detect and use current public IP
jscom-api dns update --domain mc.example.com. --use-current-ip
```

**Note**: Domain names must include the trailing dot (e.g., `mc.example.com.`)

### Global Options

```bash
# Override API base URL
jscom-api --base-url https://api.example.com ip

# Provide authentication token
jscom-api --token your-secret-token dns update --domain example.com. --ip 1.2.3.4
```

## Library Usage

### Get Public IP

```python
from jscom_api import JscomApiClient

with JscomApiClient() as client:
    result = client.get_my_ip()
    print(result.ip)  # "203.0.113.42"
```

### Update DNS Record

```python
from jscom_api import JscomApiClient

client = JscomApiClient(auth_token="your-secret-token")

try:
    response = client.update_dns(
        domain="mc.example.com.",
        ip="203.0.113.42"
    )
    print(response.message)
    print(response.change_info)
finally:
    client.close()
```

### Custom Configuration

```python
from jscom_api import JscomApiClient

client = JscomApiClient(
    base_url="https://api.example.com",
    auth_token="your-secret-token",
    timeout=60.0  # seconds
)
```

### Exception Handling

```python
from jscom_api import JscomApiClient
from jscom_api.exceptions import (
    AuthenticationError,
    ValidationError,
    NetworkError,
    ServerError
)

try:
    with JscomApiClient(auth_token="token") as client:
        client.update_dns("example.com.", "1.2.3.4")
except AuthenticationError:
    print("Invalid token")
except ValidationError as e:
    print(f"Invalid request: {e}")
except NetworkError as e:
    print(f"Connection failed: {e}")
except ServerError as e:
    print(f"Server error: {e}")
```

## Configuration

Environment variables:

- `JSCOM_API_BASE_URL`: API base URL (default: `https://api.johnsosoka.com`)
- `JSCOM_API_TOKEN`: Authentication token for protected endpoints

CLI flags override environment variables.

## Development

### Run Tests

```bash
poetry run pytest
```

### Type Checking

```bash
poetry run mypy src/
```

### Linting

```bash
poetry run ruff check src/
```

### Format Code

```bash
poetry run ruff format src/
```
