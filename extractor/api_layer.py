"""
Simplified Terabox Extractor - API Only
No browser automation (works better on free hosting)
"""

import asyncio
import aiohttp
import re
import json
import logging
from typing import Optional, Dict, Any
from urllib.parse import urlparse, quote, urlencode
import os

logger = logging.getLogger(__name__)


class TeraboxExtractor:
    """
    Terabox link extractor using API methods only
    No browser automation for better compatibility
    """
    
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.9',
    }
    
    @classmethod
    async def extract(cls, url: str) -> Optional[Dict[str, Any]]:
        """Extract download link using multiple API methods"""
        logger.info(f"[Extractor] Starting extraction for: {url}")
        
        # Normalize URL
        url = cls._normalize_url(url)
        surl = cls._extract_surl(url)
        
        if not surl:
            logger.error(f"[Extractor] Could not extract surl from URL: {url}")
            return None
        
        logger.info(f"[Extractor] Extracted surl: {surl}")
        
        # Try Method 1: SaveTube API (most reliable)
        logger.info("[Extractor] Trying SaveTube API...")
        result = await cls._try_savetube_api(url)
        if result:
            logger.info("[Extractor] ✓ Success via SaveTube API")
            return result
        
        # Try Method 2: Direct Terabox with cookie
        logger.info("[Extractor] Trying Terabox direct API...")
        result = await cls._try_terabox_direct(url, surl)
        if result:
            logger.info("[Extractor] ✓ Success via Terabox direct")
            return result
        
        # Try Method 3: TeraboxDownloader site
        logger.info("[Extractor] Trying TeraboxDownloader...")
        result = await cls._try_terabox_downloader(url)
        if result:
            logger.info("[Extractor] ✓ Success via TeraboxDownloader")
            return result
        
        logger.error("[Extractor] All extraction methods failed")
        return None
    
    @classmethod
    def _normalize_url(cls, url: str) -> str:
        """Normalize Terabox URL"""
        if not url.startswith('http'):
            url = 'https://' + url
        return url
    
    @classmethod
    def _extract_surl(cls, url: str) -> Optional[str]:
        """Extract surl from URL"""
        match = re.search(r'/s/1?([a-zA-Z0-9_-]+)', url)
        if match:
            return match.group(1)
        
        parsed = urlparse(url)
        params = dict(p.split('=') for p in parsed.query.split('&') if '=' in p)
        return params.get('surl')
    
    @classmethod
    async def _try_savetube_api(cls, url: str) -> Optional[Dict[str, Any]]:
        """Try SaveTube API"""
        try:
            api_url = f"https://ytshorts.savetube.me/api/v1/terabox-downloader?url={quote(url)}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(api_url, headers=cls.HEADERS, timeout=30) as response:
                    logger.info(f"[SaveTube] Response status: {response.status}")
                    
                    if response.status != 200:
                        logger.warning(f"[SaveTube] Bad status: {response.status}")
                        return None
                    
                    data = await response.json()
                    logger.info(f"[SaveTube] Response: {json.dumps(data)[:200]}...")
                    
                    if data.get('response') and len(data['response']) > 0:
                        file_data = data['response'][0]
                        resolutions = file_data.get('resolutions', {})
                        
                        # Get best quality
                        for quality in ['HD Video', 'SD Video', 'Fast Download']:
                            if quality in resolutions and resolutions[quality]:
                                return {
                                    'url': resolutions[quality],
                                    'filename': file_data.get('title', 'video'),
                                    'filesize': None,
                                    'filetype': 'video'
                                }
                    
                    logger.warning("[SaveTube] No valid response data")
                    return None
                    
        except Exception as e:
            logger.error(f"[SaveTube] Error: {e}")
            return None
    
    @classmethod
    async def _try_terabox_direct(cls, url: str, surl: str) -> Optional[Dict[str, Any]]:
        """Try Terabox API directly with cookie"""
        try:
            ndus = os.getenv('TERA_COOKIE', '')
            
            cookies = {}
            if ndus:
                cookies['ndus'] = ndus
                logger.info("[Terabox Direct] Using ndus cookie")
            else:
                logger.warning("[Terabox Direct] No ndus cookie set")
            
            async with aiohttp.ClientSession(cookies=cookies) as session:
                # Get page to extract jsToken
                share_url = f"https://www.terabox.com/sharing/link?surl={surl}"
                
                async with session.get(share_url, headers=cls.HEADERS, timeout=30) as response:
                    logger.info(f"[Terabox Direct] Page status: {response.status}")
                    
                    if response.status != 200:
                        return None
                    
                    html = await response.text()
                    
                    # Extract jsToken
                    token_match = re.search(r'jsToken\s*[=:]\s*["\']([^"\']+)["\']', html)
                    js_token = token_match.group(1) if token_match else ''
                    logger.info(f"[Terabox Direct] jsToken: {'found' if js_token else 'not found'}")
                    
                    # Try to get file list
                    params = {
                        'app_id': '250528',
                        'web': '1',
                        'channel': 'dubox',
                        'jsToken': js_token,
                        'page': '1',
                        'num': '100',
                        'shorturl': surl,
                        'root': '1'
                    }
                    
                    list_url = "https://www.terabox.com/share/list?" + urlencode(params)
                    
                    async with session.get(list_url, headers=cls.HEADERS, timeout=30) as list_response:
                        if list_response.status != 200:
                            logger.warning(f"[Terabox Direct] List API status: {list_response.status}")
                            return None
                        
                        data = await list_response.json()
                        logger.info(f"[Terabox Direct] List API errno: {data.get('errno')}")
                        
                        if data.get('errno') != 0:
                            return None
                        
                        file_list = data.get('list', [])
                        if not file_list:
                            logger.warning("[Terabox Direct] Empty file list")
                            return None
                        
                        # Find best file
                        best = None
                        for f in file_list:
                            if f.get('isdir') == 0:
                                if f.get('category') == 1:  # Video
                                    best = f
                                    break
                                if not best or f.get('size', 0) > best.get('size', 0):
                                    best = f
                        
                        if not best:
                            return None
                        
                        logger.info(f"[Terabox Direct] Best file: {best.get('server_filename')}")
                        
                        # Check for direct link
                        if best.get('dlink'):
                            return {
                                'url': best['dlink'],
                                'filename': best.get('server_filename'),
                                'filesize': best.get('size'),
                                'filetype': 'video' if best.get('category') == 1 else 'file'
                            }
                        
                        # Get download link
                        dl_params = {
                            'app_id': '250528',
                            'web': '1',
                            'channel': 'dubox',
                            'jsToken': js_token,
                            'shorturl': surl,
                            'fid_list': f'[{best.get("fs_id")}]',
                            'uk': str(data.get('uk', '')),
                            'shareid': str(data.get('shareid', ''))
                        }
                        
                        dl_url = "https://www.terabox.com/share/download?" + urlencode(dl_params)
                        
                        async with session.get(dl_url, headers=cls.HEADERS, timeout=30) as dl_response:
                            dl_data = await dl_response.json()
                            logger.info(f"[Terabox Direct] Download API errno: {dl_data.get('errno')}")
                            
                            dlink = dl_data.get('dlink')
                            if not dlink and dl_data.get('list'):
                                dlink = dl_data['list'][0].get('dlink')
                            
                            if dlink:
                                return {
                                    'url': dlink,
                                    'filename': best.get('server_filename'),
                                    'filesize': best.get('size'),
                                    'filetype': 'video' if best.get('category') == 1 else 'file'
                                }
                        
                        return None
                    
        except Exception as e:
            logger.error(f"[Terabox Direct] Error: {e}")
            return None
    
    @classmethod
    async def _try_terabox_downloader(cls, url: str) -> Optional[Dict[str, Any]]:
        """Try TeraboxDownloader.pro API"""
        try:
            api_url = "https://teraboxdownloader.pro/api/v1/get-info"
            
            async with aiohttp.ClientSession() as session:
                payload = {'url': url}
                headers = {
                    **cls.HEADERS,
                    'Content-Type': 'application/json',
                    'Origin': 'https://teraboxdownloader.pro',
                    'Referer': 'https://teraboxdownloader.pro/'
                }
                
                async with session.post(api_url, json=payload, headers=headers, timeout=30) as response:
                    logger.info(f"[TeraboxDownloader] Status: {response.status}")
                    
                    if response.status != 200:
                        return None
                    
                    data = await response.json()
                    logger.info(f"[TeraboxDownloader] Response: {json.dumps(data)[:200]}...")
                    
                    if data.get('ok') and data.get('data'):
                        file_data = data['data']
                        download_url = file_data.get('download_link') or file_data.get('dlink')
                        
                        if download_url:
                            return {
                                'url': download_url,
                                'filename': file_data.get('filename'),
                                'filesize': file_data.get('size'),
                                'filetype': 'video' if 'video' in str(file_data.get('type', '')).lower() else 'file'
                            }
                    
                    return None
                    
        except Exception as e:
            logger.error(f"[TeraboxDownloader] Error: {e}")
            return None


async def extract_via_api(url: str) -> Optional[Dict[str, Any]]:
    """Extract download URL using API methods only"""
    return await TeraboxExtractor.extract(url)
