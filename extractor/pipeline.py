"""
Extraction Pipeline - Simplified for Free Hosting
Uses API-only extraction (no browser overhead)
"""

import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass

from browser.context import ExtractionResult
from .api_layer import extract_via_api
from .validators import URLValidator

logger = logging.getLogger(__name__)


async def run_extraction(url: str) -> ExtractionResult:
    """
    Run extraction using API-only approach
    No browser automation (works better on free hosting)
    """
    logger.info(f"Starting extraction for: {url}")
    
    # Validate URL
    if not URLValidator.is_valid_terabox_url(url):
        return ExtractionResult(
            success=False,
            error="Invalid Terabox URL. Please provide a valid share link."
        )
    
    # Try API extraction
    try:
        result = await extract_via_api(url)
        
        if result and result.get('url'):
            logger.info(f"Extraction successful! File: {result.get('filename')}")
            return ExtractionResult(
                success=True,
                download_url=result['url'],
                filename=result.get('filename'),
                filesize=result.get('filesize'),
                filetype=result.get('filetype', 'file'),
                layer_used='api'
            )
        else:
            logger.error("API extraction returned no result")
            return ExtractionResult(
                success=False,
                error="Could not extract download link. Please try again or use a different link."
            )
            
    except Exception as e:
        logger.error(f"Extraction error: {e}")
        return ExtractionResult(
            success=False,
            error=f"Extraction failed: {str(e)}"
        )
