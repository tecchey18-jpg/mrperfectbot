"""
DOM Layer Extraction (Layer 3)
Human-like DOM automation to trigger downloads
"""

import asyncio
import logging
import random
from typing import Optional, Dict, Any, List

from playwright.async_api import Page

from .validators import FileValidator
from .network_layer import NetworkLayer
from utils.humanizer import Humanizer

logger = logging.getLogger(__name__)


class DOMLayer:
    """
    Layer 3: Smart DOM Automation
    Clicks buttons, handles modals, waits for countdowns
    """
    
    # Button selectors to try (priority order)
    DOWNLOAD_SELECTORS = [
        # Primary download buttons
        'button:has-text("Download")',
        'a:has-text("Download")',
        '[class*="download"]:has-text("Download")',
        '[id*="download"]',
        
        # Free download
        'button:has-text("Free Download")',
        'a:has-text("Free Download")',
        '[class*="free"]:has-text("Download")',
        
        # Direct/Save buttons
        'button:has-text("Save")',
        'a:has-text("Save")',
        'button:has-text("直接下载")',  # Chinese: Direct Download
        'button:has-text("普通下载")',  # Chinese: Normal Download
        
        # Play/Preview
        'button:has-text("Play")',
        'button:has-text("Preview")',
        '[class*="play-btn"]',
        '[class*="preview"]',
        
        # Generic icon buttons
        '[class*="btn"][class*="download"]',
        '[class*="icon-download"]',
        'svg[class*="download"]',
        
        # Data attributes
        '[data-action="download"]',
        '[data-type="download"]',
        
        # Terabox specific
        '.file-item-download',
        '.download-btn',
        '.btn-download',
        '#downloadBtn',
        '.primaryBtn',
        '.main-btn',
    ]
    
    # Countdown selectors
    COUNTDOWN_SELECTORS = [
        '[class*="countdown"]',
        '[class*="timer"]',
        '[id*="countdown"]',
        '[id*="timer"]',
        '.wait-time',
        '.download-wait',
    ]
    
    # Modal close selectors
    MODAL_CLOSE_SELECTORS = [
        '[class*="modal"] [class*="close"]',
        '[class*="popup"] [class*="close"]',
        '[class*="dialog"] [class*="close"]',
        '.modal-close',
        '.close-btn',
        'button[aria-label="Close"]',
        '[class*="overlay"] [class*="close"]',
    ]
    
    @classmethod
    async def wait_for_countdown(cls, page: Page, max_wait: int = 30) -> None:
        """Wait for any countdown timer to complete"""
        for selector in cls.COUNTDOWN_SELECTORS:
            try:
                countdown = await page.query_selector(selector)
                if countdown:
                    logger.info(f"[DOM Layer] Found countdown, waiting...")
                    start_time = asyncio.get_event_loop().time()
                    
                    while asyncio.get_event_loop().time() - start_time < max_wait:
                        # Check if countdown still exists
                        countdown = await page.query_selector(selector)
                        if not countdown:
                            logger.info("[DOM Layer] Countdown completed")
                            break
                        
                        # Check countdown text
                        text = await countdown.text_content()
                        if text:
                            # Try to parse remaining seconds
                            import re
                            numbers = re.findall(r'\d+', text)
                            if numbers and int(numbers[0]) == 0:
                                logger.info("[DOM Layer] Countdown reached zero")
                                break
                        
                        await asyncio.sleep(1)
                    
                    return
            except Exception:
                continue
    
    @classmethod
    async def handle_modals(cls, page: Page) -> None:
        """Close any popup modals"""
        for selector in cls.MODAL_CLOSE_SELECTORS:
            try:
                close_btn = await page.query_selector(selector)
                if close_btn and await close_btn.is_visible():
                    logger.info(f"[DOM Layer] Closing modal: {selector}")
                    await close_btn.click()
                    await asyncio.sleep(0.5)
            except Exception:
                continue
    
    @classmethod
    async def find_download_button(cls, page: Page) -> Optional[Any]:
        """Find the best download button on the page"""
        for selector in cls.DOWNLOAD_SELECTORS:
            try:
                elements = await page.query_selector_all(selector)
                for element in elements:
                    if await element.is_visible():
                        # Check if button is not disabled
                        disabled = await element.get_attribute('disabled')
                        if not disabled:
                            logger.info(f"[DOM Layer] Found button: {selector}")
                            return element
            except Exception as e:
                logger.debug(f"Error checking selector {selector}: {e}")
                continue
        
        return None
    
    @classmethod
    async def scroll_page(cls, page: Page) -> None:
        """Scroll the page naturally to load lazy content"""
        await Humanizer.human_delay(500, 0.3)
        
        # Scroll down gradually
        for _ in range(3):
            await page.mouse.wheel(0, random.randint(200, 400))
            await Humanizer.random_delay(300, 700)
        
        # Scroll back up a bit
        await page.mouse.wheel(0, -random.randint(100, 200))
        await Humanizer.random_delay(300, 500)
    
    @classmethod
    async def click_with_human_behavior(cls, page: Page, element) -> None:
        """Click an element with human-like behavior"""
        # Get bounding box
        box = await element.bounding_box()
        if not box:
            # Fallback to simple click
            await element.click()
            return
        
        # Calculate click position with offset
        x = box['x'] + box['width'] / 2 + random.uniform(-5, 5)
        y = box['y'] + box['height'] / 2 + random.uniform(-3, 3)
        
        # Move mouse naturally
        await Humanizer.move_mouse(page, x, y)
        
        # Small delay before click
        await Humanizer.random_delay(100, 300)
        
        # Click
        await page.mouse.click(x, y)
        
        # Post-click delay
        await Humanizer.human_delay(800, 0.4)


async def extract_via_dom(page: Page, timeout: int = 45000) -> Optional[Dict[str, Any]]:
    """
    Extract download URL via DOM automation
    
    Args:
        page: Playwright page (already navigated)
        timeout: Maximum time for DOM operations
    
    Returns:
        Dictionary with download info or None
    """
    logger.info("[DOM Layer] Starting DOM automation...")
    
    network = NetworkLayer()
    page.on('response', network.on_response)
    
    try:
        # Initial page scan
        await DOMLayer.scroll_page(page)
        
        # Handle any modals first
        await DOMLayer.handle_modals(page)
        
        # Check for countdown
        await DOMLayer.wait_for_countdown(page)
        
        # Try to find and click download buttons
        for attempt in range(3):
            button = await DOMLayer.find_download_button(page)
            
            if button:
                logger.info(f"[DOM Layer] Clicking download button (attempt {attempt + 1})")
                
                await DOMLayer.click_with_human_behavior(page, button)
                
                # Wait for network response
                await asyncio.sleep(2)
                
                # Check if we captured a download URL
                best = network.get_best_url()
                if best:
                    logger.info("[DOM Layer] Captured download URL after button click")
                    return {
                        'url': best.url,
                        'filename': best.filename,
                        'filesize': best.content_length,
                        'filetype': FileValidator.get_file_type(best.content_type)
                    }
                
                # Maybe a modal appeared - handle it
                await DOMLayer.handle_modals(page)
                await DOMLayer.wait_for_countdown(page)
            else:
                logger.info("[DOM Layer] No download button found")
                break
            
            await Humanizer.random_delay(1000, 2000)
        
        # Try clicking iframes
        frames = page.frames
        for frame in frames:
            if frame != page.main_frame:
                try:
                    button = await frame.query_selector(DOMLayer.DOWNLOAD_SELECTORS[0])
                    if button and await button.is_visible():
                        logger.info("[DOM Layer] Found button in iframe")
                        await button.click()
                        await asyncio.sleep(2)
                        
                        best = network.get_best_url()
                        if best:
                            return {
                                'url': best.url,
                                'filename': best.filename,
                                'filesize': best.content_length,
                                'filetype': FileValidator.get_file_type(best.content_type)
                            }
                except Exception:
                    continue
        
        logger.info("[DOM Layer] No download URL extracted via DOM")
        return None
    
    except Exception as e:
        logger.error(f"[DOM Layer] Error: {e}")
        return None
    
    finally:
        page.remove_listener('response', network.on_response)
