"""
Terabox Link Extractor Bot
Main entry point - Webhook version for free hosting
"""

import asyncio
import logging
import sys
import os
from aiohttp import web
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

from bot import setup_handlers
from browser.context import browser_manager
from config import config

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=getattr(logging, config.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Reduce noise from libraries
logging.getLogger('playwright').setLevel(logging.WARNING)
logging.getLogger('aiogram').setLevel(logging.INFO)
logging.getLogger('aiohttp').setLevel(logging.WARNING)

# Webhook settings
WEBHOOK_PATH = "/webhook"
PORT = int(os.getenv("PORT", 10000))


async def on_startup(bot: Bot) -> None:
    """Called when bot starts - set webhook"""
    logger.info("Initializing browser...")
    await browser_manager.initialize()
    
    # Get webhook URL from environment or construct from Render
    webhook_url = os.getenv("WEBHOOK_URL")
    
    if not webhook_url:
        # Try to construct from Render's RENDER_EXTERNAL_URL
        render_url = os.getenv("RENDER_EXTERNAL_URL")
        if render_url:
            webhook_url = f"{render_url}{WEBHOOK_PATH}"
        else:
            logger.error("WEBHOOK_URL or RENDER_EXTERNAL_URL not set!")
            logger.error("Set WEBHOOK_URL to your Render service URL + /webhook")
            return
    
    logger.info(f"Setting webhook to: {webhook_url}")
    await bot.set_webhook(webhook_url)
    logger.info("Bot started successfully with webhook!")


async def on_shutdown(bot: Bot) -> None:
    """Called when bot shuts down"""
    logger.info("Shutting down...")
    await bot.delete_webhook()
    await browser_manager.close()
    logger.info("Cleanup complete")


async def health_check(request):
    """Health check endpoint for Render"""
    return web.Response(text="OK", status=200)


def main() -> None:
    """Main entry point"""
    # Validate token
    token = config.bot.token
    if not token:
        logger.error("BOT_TOKEN environment variable is not set!")
        logger.error("Please set BOT_TOKEN to your Telegram bot token from @BotFather")
        sys.exit(1)
    
    # Log token info (masked for security)
    logger.info(f"Bot token loaded: {token[:10]}...{token[-5:]} (length: {len(token)})")
    
    # Validate token format
    if ':' not in token or len(token) < 30:
        logger.error("BOT_TOKEN appears to be invalid format!")
        logger.error("Token should look like: 123456789:ABCdefGHIjklMNOpqrstuvwxyz")
        sys.exit(1)
    
    # Create bot and dispatcher
    bot = Bot(
        token=token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    
    dp = Dispatcher()
    
    # Register handlers
    setup_handlers(dp)
    
    # Register startup/shutdown hooks
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    
    # Create aiohttp web application
    app = web.Application()
    
    # Add health check route (required for Render)
    app.router.add_get("/", health_check)
    app.router.add_get("/health", health_check)
    
    # Setup webhook handler
    webhook_requests_handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
    )
    webhook_requests_handler.register(app, path=WEBHOOK_PATH)
    
    # Setup application with bot lifecycle
    setup_application(app, dp, bot=bot)
    
    logger.info(f"Starting webhook server on port {PORT}...")
    
    # Run the web server
    web.run_app(app, host="0.0.0.0", port=PORT)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
