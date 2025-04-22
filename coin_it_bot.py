import os
import logging
import asyncio
import json
import time
import random
import crypto
from datetime import datetime
from typing import Dict, List, Optional, Any, Set, Union
import requests
from dotenv import load_dotenv
import viem
from viem import Address, WalletClient, PublicClient, createPublicClient, createWalletClient, http, parseEther
from viem.accounts import privateKeyToAccount
from viem.chains import base

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# API Keys and configuration
NEYNAR_API_KEY = os.getenv("NEYNAR_API_KEY")
ZORA_API_KEY = os.getenv("ZORA_API_KEY")
WALLET_PRIVATE_KEY = os.getenv("WALLET_PRIVATE_KEY")
CLANKER_FACTORY_ADDRESS = os.getenv("CLANKER_FACTORY_ADDRESS", "0x2A787b2362021cC3eEa3C24C4748a6cD5B687382")
RPC_URL = os.getenv("RPC_URL", "https://mainnet.base.org")

# Channel configuration
PLANTS_CHANNEL_ID = os.getenv("PLANTS_CHANNEL_ID", "plants")
POLLING_INTERVAL = int(os.getenv("POLLING_INTERVAL", "60"))  # Seconds between API calls

# Feature toggles
ENABLE_ZORA = os.getenv("ENABLE_ZORA", "true").lower() == "true"
ENABLE_CLANKER = os.getenv("ENABLE_CLANKER", "false").lower() == "true"

# Constants for Clanker integration
CLANKER_ABI = [
    {
        "inputs": [
            {
                "components": [
                    {
                        "components": [
                            {"internalType": "string", "name": "name", "type": "string"},
                            {"internalType": "string", "name": "symbol", "type": "string"},
                            {"internalType": "bytes32", "name": "salt", "type": "bytes32"},
                            {"internalType": "string", "name": "image", "type": "string"},
                            {"internalType": "string", "name": "metadata", "type": "string"},
                            {"internalType": "string", "name": "context", "type": "string"},
                            {"internalType": "uint256", "name": "originatingChainId", "type": "uint256"}
                        ],
                        "internalType": "struct IClanker.TokenConfig",
                        "name": "tokenConfig",
                        "type": "tuple"
                    },
                    {
                        "components": [
                            {"internalType": "uint8", "name": "vaultPercentage", "type": "uint8"},
                            {"internalType": "uint256", "name": "vaultDuration", "type": "uint256"}
                        ],
                        "internalType": "struct IClanker.VaultConfig",
                        "name": "vaultConfig",
                        "type": "tuple"
                    },
                    {
                        "components": [
                            {"internalType": "address", "name": "pairedToken", "type": "address"},
                            {"internalType": "int24", "name": "tickIfToken0IsNewToken", "type": "int24"}
                        ],
                        "internalType": "struct IClanker.PoolConfig",
                        "name": "poolConfig",
                        "type": "tuple"
                    },
                    {
                        "components": [
                            {"internalType": "uint24", "name": "pairedTokenPoolFee", "type": "uint24"},
                            {"internalType": "uint256", "name": "pairedTokenSwapAmountOutMinimum", "type": "uint256"}
                        ],
                        "internalType": "struct IClanker.InitialBuyConfig",
                        "name": "initialBuyConfig",
                        "type": "tuple"
                    },
                    {
                        "components": [
                            {"internalType": "uint256", "name": "creatorReward", "type": "uint256"},
                            {"internalType": "address", "name": "creatorAdmin", "type": "address"},
                            {"internalType": "address", "name": "creatorRewardRecipient", "type": "address"},
                            {"internalType": "address", "name": "interfaceAdmin", "type": "address"},
                            {"internalType": "address", "name": "interfaceRewardRecipient", "type": "address"}
                        ],
                        "internalType": "struct IClanker.RewardsConfig",
                        "name": "rewardsConfig",
                        "type": "tuple"
                    }
                ],
                "internalType": "struct IClanker.DeploymentConfig",
                "name": "deploymentConfig",
                "type": "tuple"
            }
        ],
        "name": "deployToken",
        "outputs": [
            {"internalType": "address", "name": "tokenAddress", "type": "address"},
            {"internalType": "uint256", "name": "positionId", "type": "uint256"}
        ],
        "stateMutability": "payable",
        "type": "function"
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "address", "name": "tokenAddress", "type": "address"},
            {"indexed": True, "internalType": "address", "name": "creatorAdmin", "type": "address"},
            {"indexed": True, "internalType": "address", "name": "interfaceAdmin", "type": "address"},
            {"indexed": False, "internalType": "address", "name": "creatorRewardRecipient", "type": "address"},
            {"indexed": False, "internalType": "address", "name": "interfaceRewardRecipient", "type": "address"},
            {"indexed": False, "internalType": "uint256", "name": "positionId", "type": "uint256"},
            {"indexed": False, "internalType": "string", "name": "name", "type": "string"},
            {"indexed": False, "internalType": "string", "name": "symbol", "type": "string"},
            {"indexed": False, "internalType": "int24", "name": "startingTickIfToken0IsNewToken", "type": "int24"},
            {"indexed": False, "internalType": "string", "name": "metadata", "type": "string"},
            {"indexed": False, "internalType": "uint256", "name": "amountTokensBought", "type": "uint256"},
            {"indexed": False, "internalType": "uint256", "name": "vaultDuration", "type": "uint256"},
            {"indexed": False, "internalType": "uint8", "name": "vaultPercentage", "type": "uint8"},
            {"indexed": False, "internalType": "address", "name": "msgSender", "type": "address"}
        ],
        "name": "TokenCreated",
        "type": "event"
    }
]

# Define core classes for our application
class NeynarAPI:
    """Client for Neynar API to monitor Farcaster channels"""
    
    BASE_URL = "https://api.neynar.com/v2/farcaster"
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {
            "x-api-key": api_key,
            "Content-Type": "application/json"
        }
        self.last_processed_time = int(time.time())  # Start with current time
        
    def get_channel_info(self, channel_id: str) -> Dict:
        """Get information about a channel by ID or name"""
        url = f"{self.BASE_URL}/channel/search"
        params = {
            "q": channel_id,
            "type": "channel_id" if channel_id.isdigit() else "name"
        }
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching channel info: {str(e)}")
            if hasattr(e, 'response') and e.response:
                logger.error(f"Response content: {e.response.text}")
            raise

    def get_channel_casts(self, channel_id: str, limit: int = 20) -> List[Dict]:
        """Get recent casts in a channel"""
        url = f"{self.BASE_URL}/feed/channel"
        params = {
            "channel_id": channel_id,
            "limit": limit,
        }
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            data = response.json()
            return data.get("casts", [])
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching channel casts: {str(e)}")
            if hasattr(e, 'response') and e.response:
                logger.error(f"Response content: {e.response.text}")
            return []

    def get_new_images(self, channel_id: str, limit: int = 20) -> List[Dict]:
        """Get new image casts since last check"""
        casts = self.get_channel_casts(channel_id, limit)
        
        # Filter for casts with images that are newer than last_processed_time
        new_image_casts = []
        current_time = int(time.time())
        
        for cast in casts:
            # Check if the cast has at least one embedded image
            has_image = False
            valid_image_urls = []
            
            # Check both embeds and embedded_media
            for embed in cast.get("embeds", []):
                if embed.get("url") and (
                    embed.get("url").endswith((".jpg", ".jpeg", ".png", ".gif")) or
                    "image" in embed.get("mime_type", "")
                ):
                    has_image = True
                    valid_image_urls.append(embed.get("url"))
            
            # Also check any other media fields
            if cast.get("embedded_media"):
                for media in cast.get("embedded_media", []):
                    if media.get("url") and (
                        media.get("url").endswith((".jpg", ".jpeg", ".png", ".gif")) or
                        "image" in media.get("type", "")
                    ):
                        has_image = True
                        valid_image_urls.append(media.get("url"))
            
            # Store the image URLs in the cast for later use
            cast["image_urls"] = valid_image_urls
            
            # Check if the cast is newer than our last check
            timestamp = cast.get("timestamp", 0)
            if has_image and timestamp > self.last_processed_time and valid_image_urls:
                new_image_casts.append(cast)
        
        # Update the last processed time
        if new_image_casts:
            self.last_processed_time = current_time
            
        return new_image_casts

    def verify_image_url(self, url: str) -> bool:
        """Verify that an image URL is accessible"""
        try:
            response = requests.head(url, timeout=5)
            return response.status_code == 200 and 'image' in response.headers.get('Content-Type', '')
        except requests.exceptions.RequestException as e:
            logger.error(f"Error verifying image URL: {str(e)}")
            return False


class ZoraAPI:
    """Client for Zora API to create and manage mints"""
    
    def __init__(self, api_key: str, wallet_client: WalletClient, chain: str = "base"):
        self.api_key = api_key
        self.wallet_client = wallet_client
        self.chain = chain
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
    def prepare_metadata(self, image_url: str, metadata: Dict) -> Dict:
        """Prepare metadata for Zora using the direct image URL"""
        return {
            "name": metadata.get("name"),
            "description": metadata.get("description"),
            "image": image_url,  # Use the original image URL
            "attributes": metadata.get("attributes", []),
            "external_url": metadata.get("source")
        }
        
    def create_zora_mint(self, name: str, image_uri: str, description: str, creator: str) -> Dict:
        """Create a new mint on Zora network using direct image URL"""
        url = "https://api.zora.co/create"
        
        payload = {
            "name": name,
            "description": description,
            "image": image_uri,  # Direct link to the image
            "creator": creator,
            "chain": self.chain,
            "properties": {
                "source": "Farcaster",
                "originalUrl": image_uri
            }
        }
        
        try:
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error creating Zora mint: {str(e)}")
            raise


class ClankerDeployer:
    """Client for deploying tokens using the Clanker SDK"""
    
    def __init__(self, wallet_client: WalletClient, public_client: PublicClient, factory_address: Address):
        self.wallet_client = wallet_client
        self.public_client = public_client
        self.factory_address = factory_address
        
    def calculate_tick(self) -> int:
        """Calculate appropriate tick for token"""
        desiredPrice = 0.0000000001
        logBase = 1.0001
        tickSpacing = 200
        rawTick = int(math.log(desiredPrice) / math.log(logBase))
        initialTick = (rawTick // tickSpacing) * tickSpacing
        return initialTick
    
    def generate_random_salt(self) -> str:
        """Generate a random salt for token deployment"""
        random_bytes = crypto.token_bytes(32)
        return f"0x{random_bytes.hex()}"
    
    async def deploy_token(self, name: str, symbol: str, image_url: str, description: str) -> str:
        """Deploy a token using the Clanker SDK"""
        if not self.wallet_client.account:
            raise ValueError("Wallet account not configured")
        
        # Create deployment data
        deployment_data = {
            "tokenConfig": {
                "name": name,
                "symbol": symbol,
                "salt": self.generate_random_salt(),
                "image": image_url,
                "metadata": json.dumps({
                    "description": description,
                    "socialMediaUrls": [],
                    "auditUrls": []
                }),
                "context": json.dumps({
                    "interface": "Farcaster-Zora Bot",
                    "platform": "Farcaster",
                    "messageId": f"farcaster-{int(time.time())}",
                    "id": f"farcaster-{int(time.time())}"
                }),
                "originatingChainId": self.public_client.chain_id if hasattr(self.public_client, 'chain_id') else 8453,
            },
            "vaultConfig": {
                "vaultPercentage": 30,  # 30% vault
                "vaultDuration": 60 * 24 * 60 * 60,  # 60 days
            },
            "poolConfig": {
                "pairedToken": "0x4200000000000000000000000000000000000006",  # WETH on Base
                "tickIfToken0IsNewToken": self.calculate_tick(),
            },
            "initialBuyConfig": {
                "pairedTokenPoolFee": 10000,  # 1% fee
                "pairedTokenSwapAmountOutMinimum": parseEther("0.01"),  # 0.01 ETH minimum
            },
            "rewardsConfig": {
                "creatorReward": 40,  # 40% creator reward
                "creatorAdmin": self.wallet_client.account.address,
                "creatorRewardRecipient": self.wallet_client.account.address,
                "interfaceAdmin": self.wallet_client.account.address,
                "interfaceRewardRecipient": self.wallet_client.account.address,
            }
        }
        
        try:
            # Simulate contract call
            simulated_result = await self.public_client.simulate_contract(
                address=self.factory_address,
                abi=CLANKER_ABI,
                function="deployToken",
                args=[deployment_data],
                value=parseEther("0.01"),  # Initial buy amount
                account=self.wallet_client.account.address
            )
            
            # Execute contract call
            tx_hash = await self.wallet_client.write_contract(simulated_result.request)
            logger.info(f"Token deployment transaction sent: {tx_hash}")
            
            # Wait for receipt
            receipt = await self.public_client.wait_for_transaction_receipt(tx_hash)
            
            # Parse logs for token address
            for log in receipt.logs:
                if log.topics and log.topics[0] == "0x..." and len(log.topics) >= 3:  # TokenCreated event signature
                    token_address = log.topics[1]
                    return token_address
            
            raise Exception("Failed to find token address in transaction logs")
            
        except Exception as e:
            logger.error(f"Error deploying token via Clanker: {str(e)}")
            raise


class CoinItBot:
    """Bot that monitors Farcaster channels and posts images to Zora and deploys Clanker tokens"""
    
    def __init__(self, neynar_key: str, wallet_key: str, rpc_url: str, channel_id: str):
        # Initialize wallet
        self.account = privateKeyToAccount(wallet_key)
        self.public_client = createPublicClient(
            chain=base,
            transport=http(rpc_url)
        )
        self.wallet_client = createWalletClient(
            account=self.account,
            chain=base,
            transport=http(rpc_url)
        )
        
        # Initialize API clients
        self.neynar = NeynarAPI(neynar_key)
        
        if ENABLE_ZORA:
            self.zora = ZoraAPI(
                api_key=ZORA_API_KEY,
                wallet_client=self.wallet_client,
                chain="base"
            )
        else:
            self.zora = None
            
        if ENABLE_CLANKER:
            self.clanker = ClankerDeployer(
                wallet_client=self.wallet_client,
                public_client=self.public_client,
                factory_address=CLANKER_FACTORY_ADDRESS
            )
        else:
            self.clanker = None
            
        self.channel_id = channel_id
        self.processed_casts = set()  # Keep track of processed cast IDs
        
    async def start(self):
        """Start the bot's main loop"""
        logger.info(f"Starting Social Bridge Bot to monitor channel /{self.channel_id}")
        logger.info(f"Features enabled: Zora: {ENABLE_ZORA}, Clanker: {ENABLE_CLANKER}")
        
        # First, get channel info to confirm it exists
        try:
            channel_info = self.neynar.get_channel_info(self.channel_id)
            logger.info(f"Connected to channel: {channel_info.get('channel', {}).get('name', 'unknown')} ({self.channel_id})")
        except Exception as e:
            logger.error(f"Failed to get channel info for {self.channel_id}: {str(e)}")
            logger.error("Please check your channel ID and API key.")
            return
        
        # Start monitoring loop
        while True:
            try:
                await self.check_for_new_images()
            except Exception as e:
                logger.error(f"Error in main loop: {str(e)}")
            
            # Wait before next check
            logger.debug(f"Waiting {POLLING_INTERVAL} seconds before next check")
            await asyncio.sleep(POLLING_INTERVAL)
    
    async def check_for_new_images(self):
        """Check for new images in the channel and process them"""
        logger.debug(f"Checking for new images in channel /{self.channel_id}")
        
        # Get new image casts
        new_image_casts = self.neynar.get_new_images(self.channel_id)
        
        if not new_image_casts:
            logger.debug("No new image casts found")
            return
        
        logger.info(f"Found {len(new_image_casts)} new image casts to process")
        
        # Process each new cast
        for cast in new_image_casts:
            cast_id = cast.get("hash")
            
            # Skip if we've already processed this cast
            if cast_id in self.processed_casts:
                continue
            
            try:
                await self.process_cast(cast)
                self.processed_casts.add(cast_id)
            except Exception as e:
                logger.error(f"Error processing cast {cast_id}: {str(e)}")
    
    async def process_cast(self, cast: Dict):
        """Process a single cast, extract images and publish to platforms"""
        cast_id = cast.get("hash")
        author = cast.get("author", {})
        author_name = author.get("username", "unknown_user")
        display_name = author.get("display_name", author_name)
        text = cast.get("text", "").strip()
        
        logger.info(f"Processing cast {cast_id} from @{author_name}")
        
        # Get images directly from the precomputed image_urls field
        images = cast.get("image_urls", [])
        
        if not images:
            logger.warning(f"No images found in cast {cast_id} despite filters")
            return
        
        # Create title and description for the content
        if text:
            title = text[:50] + ("..." if len(text) > 50 else "")
        else:
            title = f"Photo by @{author_name} from Farcaster"
            
        description = f"Posted by @{author_name} on Farcaster\n\n{text}"
        token_name = f"{author_name[:8]}{str(int(time.time()))[-4:]}"
        token_symbol = f"FC{str(int(time.time()))[-4:]}"
        
        # Process each image
        for i, image_url in enumerate(images):
            # Verify the image URL is valid before processing
            if not self.neynar.verify_image_url(image_url):
                logger.warning(f"Skipping invalid image URL: {image_url}")
                continue
                
            # Upload to Zora if enabled
            if ENABLE_ZORA and self.zora:
                try:
                    await self.publish_to_zora(image_url, title, description, author_name, cast_id)
                except Exception as e:
                    logger.error(f"Error publishing to Zora: {str(e)}")
            
            # Deploy Clanker token if enabled
            if ENABLE_CLANKER and self.clanker:
                try:
                    await self.deploy_clanker_token(image_url, token_name, token_symbol, description)
                except Exception as e:
                    logger.error(f"Error deploying Clanker token: {str(e)}")
                    
            # Only process the first valid image to avoid spam
            break
    
    async def publish_to_zora(self, image_url: str, title: str, description: str, author_name: str, cast_id: str):
        """Publish an image to Zora"""
        logger.info(f"Publishing image to Zora: {image_url}")
        
        # Prepare metadata for Zora
        metadata = {
            "name": title,
            "description": description,
            "source": f"https://warpcast.com/{author_name}/{cast_id}",
            "creator": f"@{author_name}",
            "attributes": [
                {"trait_type": "Source", "value": "Farcaster"},
                {"trait_type": "Channel", "value": f"/{self.channel_id}"},
                {"trait_type": "Author", "value": f"@{author_name}"}
            ]
        }
        
        # Prepare metadata for Zora using the direct image URL
        prepared_metadata = self.zora.prepare_metadata(image_url, metadata)
        
        # Create mint on Zora
        try:
            mint_result = self.zora.create_zora_mint(
                name=title,
                image_uri=image_url,  # Use the image URL directly
                description=description,
                creator=author_name
            )
            
            logger.info(f"Successfully published to Zora: {mint_result.get('transaction_hash', 'unknown')}")
        except Exception as e:
            logger.error(f"Failed to publish to Zora: {str(e)}")
            raise
    
    async def deploy_clanker_token(self, image_url: str, name: str, symbol: str, description: str):
        """Deploy a token using Clanker SDK"""
        logger.info(f"Deploying token via Clanker: {name} ({symbol})")
        
        try:
            token_address = await self.clanker.deploy_token(
                name=name,
                symbol=symbol,
                image_url=image_url,
                description=description
            )
            
            logger.info(f"Successfully deployed token: {token_address}")
            return token_address
        except Exception as e:
            logger.error(f"Failed to deploy token: {str(e)}")
            raise


async def main():
    """Main entry point for the bot"""
    
    # Validate required environment variables
    if not NEYNAR_API_KEY:
        logger.error("NEYNAR_API_KEY environment variable is required")
        return
    
    if ENABLE_ZORA and not ZORA_API_KEY:
        logger.error("ZORA_API_KEY environment variable is required when ENABLE_ZORA is true")
        return
    
    if not WALLET_PRIVATE_KEY:
        logger.error("WALLET_PRIVATE_KEY environment variable is required")
        return
    
    # Create and start the bot
    bot = CoinItBot(
        neynar_key=NEYNAR_API_KEY,
        wallet_key=WALLET_PRIVATE_KEY,
        rpc_url=RPC_URL,
        channel_id=PLANTS_CHANNEL_ID
    )
    
    try:
        await bot.start()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot stopped due to error: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main())