# jscom-mini-services

A collection of tiny microservices powering the API for my personal website. This repository is the home for the first mini-service—a simple endpoint to return the client's IP address, similar to whatismyip.com. Expect additional mini-services in the future!

## Current Services

- **My IP Service:**  
  Returns the requestor's IP address when invoked.
  Perfect for quickly checking your external IP or integrating with other tools.

  **Usage Example:**
  ```bash
  curl -X GET "https://YOUR_API_GATEWAY_URL/v1/ip/my"

- **DNS Update Service:**
  Dynamically updates a Route 53 DNS A record. Useful for updating services such as a Minecraft server running on a home network. The service requires an authorization token passed via the x-auth-token header.

  **Usage Example:**
  ```bash
  curl -X POST "https://api.johnsosoka.com/v1/dns/update" \
  -H "Content-Type: application/json" \
  -H "x-auth-token: <THE_AUTH_TOKEN>" \
  -d '{
  "domain": "minecraft.example.com.",
  "ip": "1.2.3.4"
  }'
  ```

## Future Services

More microservices are on the way, each designed to address a specific need while maintaining a lightweight, easily maintainable codebase.

## Contributing

Feel free to fork, open issues, or submit pull requests. This is a personal project, but community contributions are welcome!

## License

This project is licensed under the terms of the LICENSE file.