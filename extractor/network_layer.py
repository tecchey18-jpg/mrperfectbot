"""
Network Layer Extraction (Layer 1)
Intercepts network requests/responses to find download URLs
"""

import asyncio
import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from urllib.parse import urlparse

from playwright.async_api import Page, Request, Response

from .validators import FileValidator
from config import config

logger = logging.getLogger(__name__)


@dataclass
class CapturedRequest:
    """Captured network request with file information"""
    url: str
    content_type: Optional[str] = None
    content_length: Optional[int] = None
    filename: Optional[str] = None
    headers: Dict[str, str] = field(default_factory=dict)


class NetworkLayer:
    """
    Layer 1: Network Intelligence
    Intercepts all HTTP traffic to identify download URLs
    """
    
    def __init__(self):
        self.captured_urls: List[CapturedRequest] = []
        self._lock = asyncio.Lock()
    
    async def on_response(self, response: Response) -> None:
        """Handle HTTP response"""
        try:
            url = response.url
            headers = await response.all_headers()
            
            content_type = headers.get('content-type', '')
            content_length_str = headers.get('content-length', '0')
            content_disposition = headers.get('content-disposition', '')
            
            try:
                content_length = int(content_length_str) if content_length_str else 0
            except ValueError:
                content_length = 0
            
            # Check if this looks like a file download
            is_media = self._is_media_response(content_type, content_length, url)
            
            if is_media:
                async with self._lock:
                    filename = FileValidator.parse_content_disposition(content_disposition)
                    
                    captured = CapturedRequest(
                        url=url,
                        content_type=content_type,
                        content_length=content_length,
                        filename=filename,
                        headers=dict(headers)
                    )
                    
                    self.captured_urls.append(captured)
                    logger.info(f"[Network] Captured potential download: {url[:80]}...")
                    logger.info(f"[Network] Content-Type: {content_type}, Size: {FileValidator.format_file_size(content_length)}")
        
        except Exception as e:
            logger.debug(f"Error processing response: {e}")
    
    def _is_media_response(self, content_type: str, content_length: int, url: str) -> bool:
        """Check if response is likely a media file"""
        # Check content type
        media_types = [
            'video/', 'audio/', 'application/octet-stream',
            'application/x-download', 'application/force-download',
            'application/zip', 'application/x-rar', 'application/pdf'
        ]
        
        is_media_type = any(mt in content_type.lower() for mt in media_types)
        
        # Check content length (>512KB)
        is_large = content_length >= config.extraction.min_file_size
        
        # Check URL patterns
        is_cdn = FileValidator.is_cdn_url(url)
        has_sig = FileValidator.has_signature_params(url)
        
        # Must be either:
        # 1. Media type with large size
        # 2. CDN URL with signature params and large size
        return (is_media_type and is_large) or (is_cdn and has_sig and is_large)
    
    def get_best_url(self) -> Optional[CapturedRequest]:
        """Get the best captured download URL"""
        if not self.captured_urls:
            return None
        
        # Sort by content length (largest first)
        sorted_urls = sorted(
            self.captured_urls,
            key=lambda x: x.content_length or 0,
            reverse=True
        )
        
        # Prefer URLs with video content type
        for captured in sorted_urls:
            if captured.content_type and 'video' in captured.content_type.lower():
                return captured
        
        # Return largest file
        return sorted_urls[0] if sorted_urls else None
    
    def clear(self) -> None:
        """Clear captured URLs"""
        self.captured_urls.clear()


async def extract_via_network(page: Page, url: str, timeout: int = 30000) -> Optional[Dict[str, Any]]:
    """
    Extract download URL by intercepting network traffic
    
    Args:
        page: Playwright page
        url: Terabox share URL
        timeout: Maximum wait time in ms
    
    Returns:
        Dictionary with download info or None
    """
    network = NetworkLayer()
    
    # Set up response listener
    page.on('response', network.on_response)
    
    try:
        logger.info(f"[Network Layer] Loading URL: {url}")
        
        # Navigate to page
        await page.goto(url, wait_until='networkidle', timeout=timeout)
        
        # Wait a bit for any lazy-loaded content
        await asyncio.sleep(3)
        
        # Check for captured URLs
        best = network.get_best_url()
        
        if best:
            logger.info(f"[Network Layer] Found download URL via network interception")
            return {
                'url': best.url,
                'filename': best.filename,
                'filesize': best.content_length,
                'filetype': FileValidator.get_file_type(best.content_type),
                'content_type': best.content_type
            }
        
        logger.info("[Network Layer] No download URL captured from network traffic")
        return None
    
    except Exception as e:
        logger.error(f"[Network Layer] Error: {e}")
        return None
    
    finally:
        # Remove listener
        page.remove_listener('response', network.on_response)
