# Comprehensive Guide to Using the Social Bridge Bot

This tutorial will walk you through setting up and running the Social Bridge Bot, which connects Farcaster to both Zora and Clanker. By the end, you'll have a fully operational bot that monitors Farcaster's `/plants` channel, automatically publishes images to Zora, and optionally deploys Clanker tokens.

## Part 1: Understanding the Bot Architecture

The Social Bridge Bot integrates three distinct blockchain ecosystems:

1. **Farcaster**: A decentralized social network where content is discovered
2. **Zora**: An NFT platform for publishing and minting content
3. **Clanker**: A token deployment protocol on Base chain

The bot acts as a bridge between these platforms, allowing automatic cross-chain content syndication based on activity in Farcaster channels.

## Part 2: Prerequisites and Accounts Setup

Before deploying the bot, you need to set up accounts and obtain API keys for each platform:

### 2.1 Farcaster & Neynar
1. Create a Farcaster account if you don't have one
2. Register for a Neynar API key at [https://neynar.com](https://neynar.com)
3. Make note of your API key for later configuration

### 2.2 Zora
1. Create a Zora account at [https://zora.co](https://zora.co)
2. Register for developer API access
3. Make note of your API key for later configuration

### 2.3 Ethereum Wallet
1. Create or use an existing Ethereum wallet that's compatible with Base chain
2. Ensure the wallet has sufficient ETH on Base for gas fees
3. Make note of your private key (carefully secure this information)

### 2.4 Base Chain RPC
1. You can use public RPC endpoints like [https://mainnet.base.org](https://mainnet.base.org)
2. For production use, consider using a dedicated service like Alchemy or Infura

## Part 3: Installation Process

### 3.1 Environment Setup

First, let's create the project directory and set up our environment:

```bash
# Create project directory
mkdir social-bridge-bot
cd social-bridge-bot

# Clone the repository (if applicable)
git clone https://github.com/your-username/social-bridge-bot .

# Create environment file from template
cp .env.sample .env
```

Now edit the `.env` file with your credentials:

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

### 3.2 Docker Deployment

The simplest way to deploy the bot is using Docker:

```bash
# Build and start the container
docker-compose up -d

# View logs to verify everything is working
docker-compose logs -f
```

### 3.3 Manual Deployment

If you prefer to run without Docker:

```bash
# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the bot
python social-crosspost-bot.js
```

## Part 4: Configuring and Customizing the Bot

### 4.1 Feature Toggles

The bot has two main features that can be independently enabled:

- **Zora Publishing**: Set `ENABLE_ZORA=true` to publish images to Zora
- **Clanker Token Deployment**: Set `ENABLE_CLANKER=true` to deploy tokens

For your initial setup, we recommend enabling only Zora first:

```
ENABLE_ZORA=true
ENABLE_CLANKER=false
```

Once you're comfortable with how the bot operates, you can enable the Clanker token deployment as well.

### 4.2 Channel Selection

By default, the bot monitors the `/plants` channel. You can change this by modifying:

```
PLANTS_CHANNEL_ID=plants
```

Replace "plants" with the name of any other Farcaster channel you wish to monitor.

### 4.3 Polling Interval

The bot checks for new content at a specified interval. Adjust this value based on your needs:

```
POLLING_INTERVAL=60  # Checks every 60 seconds
```

Lower values provide quicker responses but increase API usage. Higher values reduce API calls but increase the delay before processing new content.

## Part 5: Operational Monitoring and Maintenance

### 5.1 Checking Bot Status

To confirm the bot is running properly:

```bash
# Check container status
docker ps

# View logs
docker-compose logs -f
```

### 5.2 Updating the Bot

To update the bot with new code:

```bash
# Pull latest code changes
git pull

# Rebuild and restart
docker-compose down
docker-compose up -d --build
```

### 5.3 Troubleshooting Common Issues

**Issue: Bot not detecting new posts**
- Check Neynar API key
- Verify the channel ID is correct
- Look for any rate limiting messages in logs

**Issue: Zora publishing fails**
- Verify Zora API key
- Check wallet has sufficient funds
- Examine logs for specific error messages

**Issue: Clanker token deployment fails**
- Ensure wallet has ETH on Base
- Verify factory address is correct
- Check RPC connection status

## Part 6: Advanced Customization

### 6.1 Customizing Zora Metadata

When publishing to Zora, the bot generates metadata based on the Farcaster post. You can customize how this metadata is formatted by modifying the `prepare_metadata` method in the `ZoraAPI` class.

### 6.2 Customizing Clanker Token Parameters

For Clanker token deployments, you can adjust parameters like vault percentage, vault duration, initial buy amount, and creator rewards. These are defined in the `deploy_token` method of the `ClankerDeployer` class.

Default configuration:
- Vault percentage: 30%
- Vault duration: 60 days
- Initial buy: 0.01 ETH
- Creator reward: 40%

### 6.3 Adding Post Filters

By default, the bot processes all image posts in the monitored channel. You can add additional filtering logic in the `get_new_images` method of the `NeynarAPI` class to filter posts based on:

- Content of text
- Specific authors
- Time of day
- Hashtags
- Engagement metrics

## Part 7: Security Considerations

### 7.1 Protecting Your Private Key

Since the bot requires your Ethereum private key, it's crucial to protect this information:

- Never commit your `.env` file to version control
- Use a dedicated wallet with limited funds
- Consider using a hardware wallet in production environments

### 7.2 API Key Management

Similar precautions apply to your API keys:

- Store them securely in the `.env` file
- Never include them in logs or error messages
- Rotate keys periodically

## Part 8: Production Deployment

For production deployments, consider these additional steps:

1. **Server Hardening**: Deploy on a secure, dedicated server
2. **Monitoring**: Implement monitoring solutions like Prometheus/Grafana
3. **Backup Strategy**: Regularly backup your configuration
4. **Logging**: Configure log rotation to prevent disk space issues
5. **Alerts**: Set up alerts for critical failures
6. **RPC Redundancy**: Use multiple RPC providers for failover

## Conclusion

You now have a fully operational Social Bridge Bot that connects Farcaster, Zora, and Clanker. This automation enables seamless content syndication across platforms, potentially increasing visibility and engagement for content creators.

As the bot runs, it will automatically discover image posts in the specified Farcaster channel, publish them to Zora with proper attribution, and optionally deploy Clanker tokens tied to the content. All of this happens without requiring manual intervention, creating an efficient bridge between these platforms.

Happy bridging!