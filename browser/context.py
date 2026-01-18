"""
Browser Context Management
Creates and manages browser contexts with full stealth configuration
"""

import asyncio
import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from contextlib import asynccontextmanager

from playwright.async_api import async_playwright, Browser, BrowserContext, Page

from .fingerprint import Fingerprint, FingerprintGenerator
from .stealth import inject_stealth_scripts, StealthConfig
from .evasion import AdvancedEvasion
from config import config

logger = logging.getLogger(__name__)


@dataclass
class ExtractionResult:
    """Result from an extraction attempt"""
    success: bool
    download_url: Optional[str] = None
    filename: Optional[str] = None
    filesize: Optional[int] = None
    filetype: Optional[str] = None
    error: Optional[str] = None
    layer_used: Optional[str] = None


class BrowserContextManager:
    """
    Manages browser lifecycle with stealth configuration
    Creates fresh contexts for each extraction job
    """
    
    def __init__(self):
        self._playwright = None
        self._browser: Optional[Browser] = None
        self._lock = asyncio.Lock()
    
    async def initialize(self) -> None:
        """Initialize Playwright and browser"""
        async with self._lock:
            if self._browser is None:
                logger.info("Initializing Playwright browser...")
                self._playwright = await async_playwright().start()
                
                self._browser = await self._playwright.chromium.launch(
                    headless=config.browser.headless,
                    slow_mo=config.browser.slow_mo,
                    args=config.browser.launch_args,
                )
                
                logger.info("Browser initialized successfully")
    
    async def close(self) -> None:
        """Close browser and cleanup"""
        async with self._lock:
            if self._browser:
                await self._browser.close()
                self._browser = None
            
            if self._playwright:
                await self._playwright.stop()
                self._playwright = None
                
            logger.info("Browser closed")
    
    @asynccontextmanager
    async def create_stealth_context(self, seed: Optional[str] = None):
        """
        Create a new browser context with full stealth configuration
        
        Args:
            seed: Optional seed for reproducible fingerprint
        
        Yields:
            Tuple of (context, page, fingerprint)
        """
        await self.initialize()
        
        # Generate unique fingerprint
        fingerprint = FingerprintGenerator.generate(seed)
        logger.info(f"Generated fingerprint: UA={fingerprint.user_agent[:50]}...")
        
        # Create context with fingerprint settings
        context_options = fingerprint.to_context_options()
        context_options['ignore_https_errors'] = True
        context_options['java_script_enabled'] = True
        context_options['bypass_csp'] = True
        
        context: Optional[BrowserContext] = None
        page: Optional[Page] = None
        
        try:
            context = await self._browser.new_context(**context_options)
            
            # Create page
            page = await context.new_page()
            
            # Inject stealth scripts
            await inject_stealth_scripts(page, fingerprint)
            
            # Inject advanced evasion
            await AdvancedEvasion.inject_all(
                page,
                fingerprint_seed=fingerprint.canvas_seed,
                timezone=fingerprint.timezone,
                locale=fingerprint.locale
            )
            
            # Set default timeouts
            page.set_default_timeout(config.browser.timeout)
            page.set_default_navigation_timeout(config.browser.navigation_timeout)
            
            logger.info("Stealth context created successfully")
            
            yield context, page, fingerprint
            
        finally:
            # Always cleanup
            if page:
                try:
                    await page.close()
                except Exception as e:
                    logger.warning(f"Error closing page: {e}")
            
            if context:
                try:
                    await context.close()
                except Exception as e:
                    logger.warning(f"Error closing context: {e}")
            
            logger.info("Context cleaned up")
    
    async def extract_with_stealth(
        self, 
        url: str,
        extractor_callback,
        max_retries: int = 3
    ) -> ExtractionResult:
        """
        Execute extraction with full stealth and retry logic
        
        Args:
            url: URL to extract from
            extractor_callback: Async function(page, fingerprint) -> ExtractionResult
            max_retries: Maximum retry attempts with new fingerprint
        
        Returns:
            ExtractionResult with success status and data
        """
        last_error = None
        
        for attempt in range(max_retries):
            try:
                # Use different seed for each retry (new identity)
                seed = f"{url}_{attempt}_{asyncio.get_event_loop().time()}"
                
                async with self.create_stealth_context(seed) as (context, page, fingerprint):
                    logger.info(f"Extraction attempt {attempt + 1}/{max_retries}")
                    
                    result = await extractor_callback(page, fingerprint)
                    
                    if result.success:
                        return result
                    
                    last_error = result.error
                    logger.warning(f"Attempt {attempt + 1} failed: {last_error}")
                    
            except Exception as e:
                last_error = str(e)
                logger.error(f"Attempt {attempt + 1} exception: {e}")
            
            # Delay before retry
            if attempt < max_retries - 1:
                delay = (attempt + 1) * 2  # Increasing delay
                logger.info(f"Waiting {delay}s before retry...")
                await asyncio.sleep(delay)
        
        return ExtractionResult(
            success=False,
            error=f"All {max_retries} attempts failed. Last error: {last_error}"
        )


# Global browser manager instance
browser_manager = BrowserContextManager()
