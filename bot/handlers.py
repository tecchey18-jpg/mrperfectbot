"""
Telegram Bot Handlers
Command and message handlers for the bot
"""

import asyncio
import logging
import re
from typing import Any

from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.enums import ParseMode

from .messages import Messages
from extractor.pipeline import run_extraction
from extractor.validators import URLValidator
from config import config

logger = logging.getLogger(__name__)

# Create router
router = Router()

# Active extractions to prevent duplicates
active_extractions: dict = {}


@router.message(Command("start"))
async def cmd_start(message: Message) -> None:
    """Handle /start command"""
    await message.answer(Messages.WELCOME, parse_mode=ParseMode.HTML)


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    """Handle /help command"""
    await message.answer(Messages.HELP, parse_mode=ParseMode.HTML)


@router.message(F.text)
async def handle_url(message: Message) -> None:
    """Handle URL messages"""
    text = message.text.strip()
    user_id = message.from_user.id
    
    # Extract URL from message (might contain other text)
    url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
    urls = re.findall(url_pattern, text)
    
    if not urls:
        # Not a URL, ignore silently
        return
    
    url = urls[0]
    
    # Normalize URL
    url = URLValidator.normalize_url(url)
    
    # Validate domain
    if not URLValidator.is_valid_terabox_url(url):
        await message.answer(Messages.INVALID_URL, parse_mode=ParseMode.HTML)
        return
    
    # Check for duplicate extraction
    extraction_key = f"{user_id}:{url}"
    if extraction_key in active_extractions:
        await message.answer(
            "⏳ This link is already being processed. Please wait...",
            parse_mode=ParseMode.HTML
        )
        return
    
    # Mark extraction as active
    active_extractions[extraction_key] = True
    
    # Send processing message
    processing_msg = await message.answer(Messages.PROCESSING, parse_mode=ParseMode.HTML)
    
    try:
        logger.info(f"Starting extraction for user {user_id}: {url}")
        
        # Run extraction
        result = await run_extraction(url)
        
        if result.success:
            logger.info(f"Extraction successful via {result.layer_used}")
            
            response = Messages.success(
                download_url=result.download_url,
                filename=result.filename,
                filesize=result.filesize,
                filetype=result.filetype
            )
            
            await processing_msg.edit_text(response, parse_mode=ParseMode.HTML)
        else:
            logger.warning(f"Extraction failed: {result.error}")
            
            response = Messages.ERROR.format(error=result.error)
            await processing_msg.edit_text(response, parse_mode=ParseMode.HTML)
    
    except asyncio.CancelledError:
        logger.info("Extraction cancelled")
        await processing_msg.edit_text(
            "❌ Extraction was cancelled.",
            parse_mode=ParseMode.HTML
        )
    
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        
        await processing_msg.edit_text(
            Messages.ERROR.format(error="An unexpected error occurred. Please try again."),
            parse_mode=ParseMode.HTML
        )
    
    finally:
        # Remove from active extractions
        active_extractions.pop(extraction_key, None)


def setup_handlers(dp: Dispatcher) -> None:
    """Register all handlers with the dispatcher"""
    dp.include_router(router)
    logger.info("Handlers registered")
