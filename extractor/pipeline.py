"""
Extraction Pipeline Orchestrator
Coordinates all extraction layers with retry and recovery
"""

import asyncio
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass

from playwright.async_api import Page

from browser.fingerprint import Fingerprint
from browser.context import ExtractionResult
from .network_layer import extract_via_network, NetworkLayer
from .js_layer import extract_via_js
from .dom_layer import extract_via_dom
from .validators import URLValidator, FileValidator
from utils.humanizer import Humanizer
from config import config

logger = logging.getLogger(__name__)


class ExtractionPipeline:
    """
    Multi-layer extraction pipeline for Terabox
    
    Layers:
    1. Network - Intercept HTTP traffic
    2. JavaScript - Inspect window variables
    3. DOM - Click buttons with human behavior
    4. Recovery - Retry with new fingerprint
    """
    
    @classmethod
    async def extract(cls, page: Page, fingerprint: Fingerprint, url: str) -> ExtractionResult:
        """
        Execute the full extraction pipeline
        
        Args:
            page: Playwright page with stealth configured
            fingerprint: Current session fingerprint
            url: Terabox share URL
        
        Returns:
            ExtractionResult with success status and data
        """
        logger.info(f"Starting extraction pipeline for: {url}")
        
        # Validate URL first
        if not URLValidator.is_valid_terabox_url(url):
            return ExtractionResult(
                success=False,
                error="Invalid Terabox URL. Please provide a valid share link."
            )
        
        # Set up network interception for all layers
        network = NetworkLayer()
        page.on('response', network.on_response)
        
        try:
            # ========== LAYER 1: NETWORK ==========
            logger.info("=" * 50)
            logger.info("LAYER 1: Network Intelligence")
            logger.info("=" * 50)
            
            result = await cls._try_network_layer(page, url, network)
            if result:
                return cls._build_result(result, 'network')
            
            # ========== LAYER 2: JAVASCRIPT ==========
            logger.info("=" * 50)
            logger.info("LAYER 2: JavaScript State Inspection")
            logger.info("=" * 50)
            
            result = await cls._try_js_layer(page)
            if result:
                return cls._build_result(result, 'javascript')
            
            # ========== LAYER 3: DOM AUTOMATION ==========
            logger.info("=" * 50)
            logger.info("LAYER 3: DOM Automation")
            logger.info("=" * 50)
            
            result = await cls._try_dom_layer(page, network)
            if result:
                return cls._build_result(result, 'dom')
            
            # Check if network captured anything after all layers
            best = network.get_best_url()
            if best:
                return ExtractionResult(
                    success=True,
                    download_url=best.url,
                    filename=best.filename,
                    filesize=best.content_length,
                    filetype=FileValidator.get_file_type(best.content_type),
                    layer_used='network_late'
                )
            
            # All layers failed
            logger.error("All extraction layers failed")
            return ExtractionResult(
                success=False,
                error="Could not extract download link. The page structure may have changed."
            )
        
        except Exception as e:
            logger.error(f"Pipeline exception: {e}")
            return ExtractionResult(
                success=False,
                error=f"Extraction error: {str(e)}"
            )
        
        finally:
            page.remove_listener('response', network.on_response)
    
    @classmethod
    async def _try_network_layer(
        cls, 
        page: Page, 
        url: str, 
        network: NetworkLayer
    ) -> Optional[Dict[str, Any]]:
        """Execute network layer extraction"""
        try:
            # Navigate to page
            logger.info(f"Navigating to: {url}")
            
            await page.goto(url, wait_until='domcontentloaded', timeout=config.extraction.network_layer_timeout)
            
            # Wait for network idle
            try:
                await page.wait_for_load_state('networkidle', timeout=10000)
            except Exception:
                logger.debug("Network idle timeout - continuing")
            
            # Human-like initial wait
            await Humanizer.human_delay(2000, 0.3)
            
            # Check captured URLs
            best = network.get_best_url()
            if best:
                logger.info(f"[Network] Found download URL: {best.url[:60]}...")
                return {
                    'url': best.url,
                    'filename': best.filename,
                    'filesize': best.content_length,
                    'filetype': FileValidator.get_file_type(best.content_type)
                }
            
            return None
        
        except Exception as e:
            logger.error(f"[Network Layer] Error: {e}")
            return None
    
    @classmethod
    async def _try_js_layer(cls, page: Page) -> Optional[Dict[str, Any]]:
        """Execute JavaScript layer extraction"""
        try:
            result = await extract_via_js(page)
            return result
        except Exception as e:
            logger.error(f"[JS Layer] Error: {e}")
            return None
    
    @classmethod
    async def _try_dom_layer(cls, page: Page, network: NetworkLayer) -> Optional[Dict[str, Any]]:
        """Execute DOM layer extraction"""
        try:
            result = await extract_via_dom(page)
            return result
        except Exception as e:
            logger.error(f"[DOM Layer] Error: {e}")
            return None
    
    @classmethod
    def _build_result(cls, data: Dict[str, Any], layer: str) -> ExtractionResult:
        """Build ExtractionResult from layer output"""
        # Validate the URL
        url = data.get('url', '')
        is_valid, reason = FileValidator.validate_extracted_url(
            url, 
            data.get('filesize')
        )
        
        if not is_valid:
            logger.warning(f"Extracted URL failed validation: {reason}")
            # Still return it, but log warning
        
        return ExtractionResult(
            success=True,
            download_url=url,
            filename=data.get('filename'),
            filesize=data.get('filesize'),
            filetype=data.get('filetype', 'file'),
            layer_used=layer
        )


async def run_extraction(url: str) -> ExtractionResult:
    """
    Run full extraction with browser context management
    This is the main entry point for extraction
    """
    from browser.context import browser_manager
    
    async def extractor(page: Page, fingerprint: Fingerprint) -> ExtractionResult:
        return await ExtractionPipeline.extract(page, fingerprint, url)
    
    return await browser_manager.extract_with_stealth(
        url=url,
        extractor_callback=extractor,
        max_retries=config.extraction.max_retries
    )
