# Coin-It Social Bridge Bot

A multi-chain bridge bot that monitors Farcaster channels (specifically `/plants`) and automatically performs two actions:

1. Publishes images to Zora as NFTs with proper attribution
2. Deploys Clanker tokens for each image with customizable parameters

## Features

- **Real-time Monitoring**: Continuously watches Farcaster channels for new content
- **Image Detection**: Automatically identifies posts containing images
- **Zora Integration**: Publishes images to Zora with proper metadata and attribution
- **Clanker Integration**: Optionally deploys tokens on Base chain using the Clanker SDK
- **Feature Toggles**: Enable/disable Zora and Clanker functionalities independently
- **Docker Support**: Easy deployment using Docker and Docker Compose

## Prerequisites

- Neynar API Key (for Farcaster access)
- Zora API Key (if Zora publishing is enabled)
- Ethereum wallet private key
- Base RPC URL (default uses Base mainnet)
- Docker and Docker Compose (for containerized deployment)

## Setup Guide

### 1. Clone the Repository

```bash
git clone https://github.com/developerfred/coin-it-bridge-bot
cd coin-it-bridge-bot
```

### 2. Configure Environment Variables

Create a `.env` file from the template:

```bash
cp .env.sample .env
```

Edit the `.env` file with your API keys and configuration:

```
# API Keys
NEYNAR_API_KEY=your_neynar_api_key
ZORA_API_KEY=your_zora_api_key

# Wallet Configuration
WALLET_PRIVATE_KEY=0xYourPrivateKeyHere
RPC_URL=https://mainnet.base.org

# Channel Configuration
PLANTS_CHANNEL_ID=plants
POLLING_INTERVAL=60

# Feature Toggles
ENABLE_ZORA=true
ENABLE_CLANKER=false

# Clanker Configuration
CLANKER_FACTORY_ADDRESS=0x2A787b2362021cC3eEa3C24C4748a6cD5B687382
```

### 3. Build and Run with Docker

```bash
docker-compose up -d
```

This command builds the Docker image and starts the container in detached mode.

### 4. Monitor Logs

```bash
docker-compose logs -f
```

## Understanding the Bot

### How It Works

1. **Initialization**: The bot connects to Farcaster using the Neynar API
2. **Monitoring**: It continuously polls the specified channel for new posts
3. **Processing**: When a post with an image is detected, the bot:
   - Extracts the image URL
   - Gathers metadata (author name, caption, etc.)
   - Publishes to Zora (if enabled)
   - Deploys a Clanker token (if enabled)
4. **Tracking**: The bot keeps track of processed posts to avoid duplicates

### Feature Toggles

The bot supports two main features that can be enabled or disabled independently:

- **ENABLE_ZORA**: When `true`, images are published to Zora as NFTs
- **ENABLE_CLANKER**: When `true`, tokens are deployed on Base chain using Clanker

## Customization

### Polling Interval

Adjust the `POLLING_INTERVAL` environment variable to control how frequently the bot checks for new posts (in seconds).

### Channel Selection

Change the `PLANTS_CHANNEL_ID` environment variable to monitor a different Farcaster channel.

### Token Configuration

The default token configuration includes:
- 30% vault percentage
- 60 days vault duration
- 0.01 ETH initial buy amount
- 40% creator reward

These parameters can be modified in the `deploy_token` method in the `ClankerDeployer` class.

## Troubleshooting

### Common Issues

1. **API Key Errors**: Ensure your Neynar and Zora API keys are correct
2. **RPC Connection Issues**: Verify your RPC URL is active and accessible
3. **Wallet Balance**: Ensure your wallet has sufficient ETH for Clanker token deployments

### Log Files

Logs are stored in the `logs` directory and can be accessed for debugging purposes.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

---

### Created by [@codingsh](https://x.com/codingsh)

🌿 Find me on:
- Twitter: [x.com/codingsh](https://x.com/codingsh)
- Farcaster: [warpcast.com/codingsh](https://warpcast.com/codingsh)

*If you found this bot helpful, consider giving it a star on GitHub!*
