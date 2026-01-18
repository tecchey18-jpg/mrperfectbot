"""
Terabox Link Extractor Bot
Main entry point
"""

import asyncio
import logging
import sys
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

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


async def on_startup() -> None:
    """Called when bot starts"""
    logger.info("Initializing browser...")
    await browser_manager.initialize()
    logger.info("Bot started successfully!")


async def on_shutdown() -> None:
    """Called when bot shuts down"""
    logger.info("Shutting down...")
    await browser_manager.close()
    logger.info("Cleanup complete")


async def main() -> None:
    """Main entry point"""
    # Validate token
    if not config.bot.token:
        logger.error("BOT_TOKEN environment variable is not set!")
        logger.error("Please set BOT_TOKEN to your Telegram bot token from @BotFather")
        sys.exit(1)
    
    # Create bot and dispatcher
    bot = Bot(
        token=config.bot.token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    
    dp = Dispatcher()
    
    # Register handlers
    setup_handlers(dp)
    
    # Register startup/shutdown hooks
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    
    logger.info("Starting bot...")
    
    try:
        # Start polling
        await dp.start_polling(
            bot,
            allowed_updates=["message"],
            drop_pending_updates=True
        )
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
