"""
JavaScript Layer Extraction (Layer 2)
Inspects JavaScript state and uses Terabox internal API
"""

import asyncio
import json
import re
import logging
from typing import Optional, Dict, Any, List
from urllib.parse import urlparse, parse_qs

from playwright.async_api import Page

from .validators import FileValidator
from config import config

logger = logging.getLogger(__name__)


class JSLayer:
    """
    Layer 2: JavaScript State Inspection + Terabox API
    Extracts URLs using window variables and internal API calls
    """
    
    @classmethod
    async def extract_terabox_api(cls, page: Page, url: str) -> Optional[Dict[str, Any]]:
        """
        Use Terabox's internal API to get download link
        This is the most reliable method
        """
        try:
            # Extract surl from URL
            surl = cls._extract_surl(url)
            if not surl:
                logger.warning("[JS Layer] Could not extract surl from URL")
                return None
            
            logger.info(f"[JS Layer] Extracted surl: {surl}")
            
            # Get jsToken and other required params from page
            page_data = await page.evaluate('''
                () => {
                    return {
                        jsToken: window.jsToken || null,
                        bdstoken: window.bdstoken || null,
                        shareId: window.shareid || window.share_id || null,
                        uk: window.uk || null,
                        sign: window.sign || null,
                        timestamp: window.timestamp || null,
                        fileList: window.fileList || null,
                        locals: window.locals || null
                    };
                }
            ''')
            
            logger.info(f"[JS Layer] Page data: jsToken={'found' if page_data.get('jsToken') else 'not found'}")
            
            js_token = page_data.get('jsToken')
            
            if not js_token:
                # Try to extract from HTML source
                js_token = await cls._extract_jstoken_from_source(page)
            
            if not js_token:
                logger.warning("[JS Layer] Could not find jsToken")
                return None
            
            # Get share info first
            share_info = await cls._get_share_info(page, surl, js_token)
            if not share_info:
                logger.warning("[JS Layer] Could not get share info")
                return None
            
            # Extract file info from share
            file_info = cls._extract_file_from_share(share_info)
            if not file_info:
                logger.warning("[JS Layer] Could not extract file info")
                return None
            
            # Get download link
            download_url = await cls._get_download_link(
                page, 
                surl, 
                js_token,
                file_info.get('fs_id'),
                share_info.get('uk'),
                share_info.get('shareid')
            )
            
            if download_url:
                return {
                    'url': download_url,
                    'filename': file_info.get('server_filename'),
                    'filesize': file_info.get('size'),
                    'filetype': 'video' if file_info.get('category') == 1 else 'file'
                }
            
            return None
            
        except Exception as e:
            logger.error(f"[JS Layer] API extraction error: {e}")
            return None
    
    @classmethod
    def _extract_surl(cls, url: str) -> Optional[str]:
        """Extract surl from Terabox URL"""
        # Try /s/XXXXX pattern
        match = re.search(r'/s/1?([a-zA-Z0-9_-]+)', url)
        if match:
            surl = match.group(1)
            # Remove leading '1' if present (some URLs have 1XXXXXX)
            if url.endswith(surl) and '/s/1' in url:
                return surl
            return surl
        
        # Try surl query param
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        if 'surl' in params:
            return params['surl'][0]
        
        return None
    
    @classmethod
    async def _extract_jstoken_from_source(cls, page: Page) -> Optional[str]:
        """Extract jsToken from page HTML source"""
        try:
            content = await page.content()
            
            # Look for jsToken in various formats
            patterns = [
                r'window\.jsToken\s*=\s*["\']([^"\']+)["\']',
                r'"jsToken"\s*:\s*"([^"]+)"',
                r"'jsToken'\s*:\s*'([^']+)'",
                r'jsToken=([a-zA-Z0-9]+)',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, content)
                if match:
                    return match.group(1)
            
            return None
        except Exception as e:
            logger.debug(f"Error extracting jsToken from source: {e}")
            return None
    
    @classmethod
    async def _get_share_info(cls, page: Page, surl: str, js_token: str) -> Optional[Dict]:
        """Get share information via API"""
        try:
            result = await page.evaluate(f'''
                async () => {{
                    try {{
                        const response = await fetch('/share/list?app_id=250528&web=1&channel=dubox&jsToken={js_token}&dp-logid=&page=1&num=100&by=name&order=asc&site_referer=&shorturl={surl}&root=1', {{
                            method: 'GET',
                            headers: {{
                                'Accept': 'application/json, text/plain, */*',
                                'X-Requested-With': 'XMLHttpRequest'
                            }},
                            credentials: 'include'
                        }});
                        const data = await response.json();
                        return data;
                    }} catch(e) {{
                        return {{ error: e.message }};
                    }}
                }}
            ''')
            
            if result and result.get('errno') == 0:
                return result
            
            logger.warning(f"[JS Layer] Share list API returned: {result}")
            return None
            
        except Exception as e:
            logger.error(f"[JS Layer] Error getting share info: {e}")
            return None
    
    @classmethod
    def _extract_file_from_share(cls, share_info: Dict) -> Optional[Dict]:
        """Extract the largest video/file from share info"""
        try:
            file_list = share_info.get('list', [])
            
            if not file_list:
                return None
            
            # Filter for videos (category 1) or get largest file
            videos = [f for f in file_list if f.get('category') == 1]
            
            if videos:
                # Return largest video
                return max(videos, key=lambda x: x.get('size', 0))
            
            # If no videos, return largest file
            return max(file_list, key=lambda x: x.get('size', 0))
            
        except Exception as e:
            logger.error(f"[JS Layer] Error extracting file: {e}")
            return None
    
    @classmethod
    async def _get_download_link(
        cls, 
        page: Page, 
        surl: str, 
        js_token: str,
        fs_id: str,
        uk: str,
        share_id: str
    ) -> Optional[str]:
        """Get direct download link via API"""
        try:
            if not all([fs_id, uk, share_id]):
                logger.warning("[JS Layer] Missing required params for download link")
                return None
            
            result = await page.evaluate(f'''
                async () => {{
                    try {{
                        const response = await fetch('/share/download?app_id=250528&web=1&channel=dubox&jsToken={js_token}&dp-logid=&shorturl={surl}&fid_list=[{fs_id}]&uk={uk}&shareid={share_id}', {{
                            method: 'GET',
                            headers: {{
                                'Accept': 'application/json, text/plain, */*',
                                'X-Requested-With': 'XMLHttpRequest'
                            }},
                            credentials: 'include'
                        }});
                        const data = await response.json();
                        return data;
                    }} catch(e) {{
                        return {{ error: e.message }};
                    }}
                }}
            ''')
            
            if result and result.get('errno') == 0:
                # Extract dlink
                dlink = result.get('dlink')
                if dlink:
                    return dlink
                
                # Try list format
                dlink_list = result.get('list', [])
                if dlink_list and dlink_list[0].get('dlink'):
                    return dlink_list[0]['dlink']
            
            logger.warning(f"[JS Layer] Download API returned: {result}")
            
            # Try alternative endpoint
            return await cls._try_alternative_download(page, surl, js_token, fs_id, uk, share_id)
            
        except Exception as e:
            logger.error(f"[JS Layer] Error getting download link: {e}")
            return None
    
    @classmethod
    async def _try_alternative_download(
        cls, 
        page: Page, 
        surl: str, 
        js_token: str,
        fs_id: str,
        uk: str,
        share_id: str
    ) -> Optional[str]:
        """Try alternative download methods"""
        try:
            # Try streaming link for videos
            result = await page.evaluate(f'''
                async () => {{
                    try {{
                        const response = await fetch('/share/streaming?app_id=250528&channel=dubox&uk={uk}&shareid={share_id}&fid={fs_id}&type=M3U8_AUTO_720', {{
                            method: 'GET',
                            credentials: 'include'
                        }});
                        const data = await response.json();
                        return data;
                    }} catch(e) {{
                        return {{ error: e.message }};
                    }}
                }}
            ''')
            
            if result and result.get('errno') == 0:
                # Look for direct link in various formats
                for key in ['dlink', 'ltime', 'info', 'stream_url']:
                    if result.get(key):
                        return result[key]
            
            return None
            
        except Exception as e:
            logger.debug(f"[JS Layer] Alternative download failed: {e}")
            return None


# Common window variable patterns
WINDOW_VARS = [
    'window.fileInfo',
    'window.yunData',
    'window.locals',
    'window.pageData',
    'window.shareData',
    'window.videoData',
]


async def extract_via_js(page: Page, url: str = "") -> Optional[Dict[str, Any]]:
    """
    Extract download URL by inspecting JavaScript state
    
    Args:
        page: Playwright page (already navigated)
        url: Original Terabox URL
    
    Returns:
        Dictionary with download info or None
    """
    logger.info("[JS Layer] Inspecting JavaScript state...")
    
    # Try Terabox API method first (most reliable)
    if url:
        result = await JSLayer.extract_terabox_api(page, url)
        if result:
            logger.info("[JS Layer] Successfully extracted via API")
            return result
    
    # Fallback: Try to find video source directly
    try:
        video_src = await page.evaluate('''
            () => {
                // Check for video elements
                const video = document.querySelector('video');
                if (video && video.src) return video.src;
                
                // Check for source elements
                const source = document.querySelector('video source');
                if (source && source.src) return source.src;
                
                // Check for player data
                if (window.player && window.player.src) return window.player.src;
                
                return null;
            }
        ''')
        
        if video_src and FileValidator.is_cdn_url(video_src):
            return {
                'url': video_src,
                'filename': None,
                'filesize': None,
                'filetype': 'video'
            }
    except Exception as e:
        logger.debug(f"[JS Layer] Video source extraction failed: {e}")
    
    logger.info("[JS Layer] No download URL found in JavaScript state")
    return None
