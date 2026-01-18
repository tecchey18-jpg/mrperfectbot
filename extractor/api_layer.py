"""
Terabox Extractor using Third-Party API
Uses free APIs that working Terabox bots use
"""

import asyncio
import aiohttp
import re
import json
import logging
from typing import Optional, Dict, Any
from urllib.parse import urlparse, quote
import os

logger = logging.getLogger(__name__)


class TeraboxExtractor:
    """
    Terabox link extractor using multiple methods
    Tries different APIs until one works
    """
    
    # Supported domains
    DOMAINS = [
        'terabox.com', '1024tera.com', 'teraboxapp.com', '4funbox.com',
        'mirrobox.com', 'nephobox.com', 'freeterabox.com', 'momerybox.com',
        'teraboxlink.com', 'terasharelink.com', '1024terabox.com'
    ]
    
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.9',
    }
    
    @classmethod
    async def extract(cls, url: str) -> Optional[Dict[str, Any]]:
        """
        Extract download link using multiple methods
        """
        logger.info(f"[Extractor] Starting extraction for: {url}")
        
        # Normalize URL
        url = cls._normalize_url(url)
        
        # Try Method 1: TeraboxDownloader API
        result = await cls._try_terabox_downloader_api(url)
        if result:
            logger.info("[Extractor] Success via TeraboxDownloader API")
            return result
        
        # Try Method 2: Direct page parsing with better logic
        result = await cls._try_direct_parsing(url)
        if result:
            logger.info("[Extractor] Success via direct parsing")
            return result
        
        # Try Method 3: Alternative API endpoints
        result = await cls._try_alternative_apis(url)
        if result:
            logger.info("[Extractor] Success via alternative API")
            return result
        
        logger.error("[Extractor] All extraction methods failed")
        return None
    
    @classmethod
    def _normalize_url(cls, url: str) -> str:
        """Normalize Terabox URL"""
        # Ensure https
        if not url.startswith('http'):
            url = 'https://' + url
        
        # Convert various domains to standard format
        for domain in cls.DOMAINS:
            if domain in url:
                # Extract the share path
                match = re.search(r'/s/([a-zA-Z0-9_-]+)', url)
                if match:
                    return f"https://www.terabox.com/s/{match.group(1)}"
        
        return url
    
    @classmethod
    async def _try_terabox_downloader_api(cls, url: str) -> Optional[Dict[str, Any]]:
        """
        Try the terabox downloader approach
        This mimics what successful bots do
        """
        try:
            async with aiohttp.ClientSession() as session:
                # First, get the page and extract the data
                headers = {
                    **cls.HEADERS,
                    'Cookie': f'ndus={os.getenv("TERA_COOKIE", "")}'
                }
                
                async with session.get(url, headers=headers, allow_redirects=True, timeout=30) as response:
                    if response.status != 200:
                        logger.warning(f"Page returned status {response.status}")
                        return None
                    
                    html = await response.text()
                    
                    # Extract data from HTML
                    data = cls._parse_terabox_html(html)
                    
                    if data and data.get('download_link'):
                        return {
                            'url': data['download_link'],
                            'filename': data.get('filename'),
                            'filesize': data.get('filesize'),
                            'filetype': data.get('filetype', 'file')
                        }
                    
                    # Try to call internal API
                    if data:
                        api_result = await cls._call_terabox_api(session, data, url)
                        if api_result:
                            return api_result
                    
                    return None
                    
        except Exception as e:
            logger.error(f"TeraboxDownloader API error: {e}")
            return None
    
    @classmethod
    def _parse_terabox_html(cls, html: str) -> Optional[Dict]:
        """Parse Terabox HTML to extract file data"""
        result = {}
        
        try:
            # Try to find yunData
            yun_match = re.search(r'var\s+yunData\s*=\s*(\{[^;]+\});', html)
            if not yun_match:
                yun_match = re.search(r'window\.yunData\s*=\s*(\{[^;]+\});', html)
            
            if yun_match:
                try:
                    yun_data = json.loads(yun_match.group(1))
                    result['yunData'] = yun_data
                    result['shareid'] = yun_data.get('shareid')
                    result['uk'] = yun_data.get('uk')
                    result['sign'] = yun_data.get('sign')
                    result['timestamp'] = yun_data.get('timestamp')
                    
                    # Get file list
                    file_list = yun_data.get('file_list', {})
                    if isinstance(file_list, dict):
                        files = file_list.get('list', [])
                    else:
                        files = file_list if isinstance(file_list, list) else []
                    
                    if files:
                        # Get video or largest file
                        best = None
                        for f in files:
                            if f.get('isdir') == 0 or not f.get('isdir'):
                                if f.get('category') == 1:  # Video
                                    best = f
                                    break
                                if not best or (f.get('size', 0) > best.get('size', 0)):
                                    best = f
                        
                        if best:
                            result['fs_id'] = best.get('fs_id')
                            result['filename'] = best.get('server_filename')
                            result['filesize'] = best.get('size')
                            result['filetype'] = 'video' if best.get('category') == 1 else 'file'
                            
                            # Check for direct link
                            if best.get('dlink'):
                                result['download_link'] = best['dlink']
                except json.JSONDecodeError:
                    pass
            
            # Extract jsToken
            token_patterns = [
                r'window\.jsToken\s*=\s*["\']([^"\']+)["\']',
                r'"jsToken"\s*:\s*"([^"]+)"',
                r"jsToken\s*=\s*'([^']+)'",
            ]
            for pattern in token_patterns:
                match = re.search(pattern, html)
                if match:
                    result['jsToken'] = match.group(1)
                    break
            
            # Try to find direct link in page
            dlink_match = re.search(r'"dlink"\s*:\s*"([^"]+)"', html)
            if dlink_match:
                dlink = dlink_match.group(1).replace('\\/', '/')
                if not result.get('download_link'):
                    result['download_link'] = dlink
            
        except Exception as e:
            logger.debug(f"Parse error: {e}")
        
        return result if result else None
    
    @classmethod
    async def _call_terabox_api(cls, session: aiohttp.ClientSession, data: Dict, url: str) -> Optional[Dict[str, Any]]:
        """Call Terabox API to get download link"""
        try:
            # Extract surl
            surl_match = re.search(r'/s/1?([a-zA-Z0-9_-]+)', url)
            if not surl_match:
                return None
            
            surl = surl_match.group(1)
            js_token = data.get('jsToken', '')
            
            # Build API URL
            params = {
                'app_id': '250528',
                'web': '1',
                'channel': 'dubox',
                'jsToken': js_token,
                'dp-logid': '',
                'page': '1',
                'num': '100',
                'by': 'name',
                'order': 'asc',
                'shorturl': surl,
                'root': '1'
            }
            
            list_url = "https://www.terabox.com/share/list?" + "&".join([f"{k}={v}" for k, v in params.items()])
            
            headers = {
                **cls.HEADERS,
                'Cookie': f'ndus={os.getenv("TERA_COOKIE", "")}',
                'Referer': url
            }
            
            async with session.get(list_url, headers=headers, timeout=30) as response:
                if response.status != 200:
                    return None
                
                api_data = await response.json()
                
                if api_data.get('errno') != 0:
                    logger.warning(f"API errno: {api_data.get('errno')}")
                    return None
                
                file_list = api_data.get('list', [])
                
                # Find best file
                best = None
                for f in file_list:
                    if f.get('isdir') == 0:
                        if f.get('category') == 1:
                            best = f
                            break
                        if not best or f.get('size', 0) > best.get('size', 0):
                            best = f
                
                if not best:
                    return None
                
                # Check for dlink
                if best.get('dlink'):
                    return {
                        'url': best['dlink'],
                        'filename': best.get('server_filename'),
                        'filesize': best.get('size'),
                        'filetype': 'video' if best.get('category') == 1 else 'file'
                    }
                
                # Need to get download link
                fs_id = best.get('fs_id')
                uk = api_data.get('uk')
                shareid = api_data.get('shareid')
                
                if not all([fs_id, uk, shareid]):
                    return None
                
                download_params = {
                    'app_id': '250528',
                    'web': '1',
                    'channel': 'dubox',
                    'jsToken': js_token,
                    'dp-logid': '',
                    'shorturl': surl,
                    'fid_list': f'[{fs_id}]',
                    'uk': str(uk),
                    'shareid': str(shareid)
                }
                
                download_url = "https://www.terabox.com/share/download?" + "&".join([f"{k}={v}" for k, v in download_params.items()])
                
                async with session.get(download_url, headers=headers, timeout=30) as dl_response:
                    dl_data = await dl_response.json()
                    
                    if dl_data.get('errno') == 0:
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
            logger.error(f"API call error: {e}")
            return None
    
    @classmethod
    async def _try_direct_parsing(cls, url: str) -> Optional[Dict[str, Any]]:
        """Try direct HTML parsing with mobile user agent"""
        try:
            async with aiohttp.ClientSession() as session:
                # Try mobile user agent
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Cookie': f'ndus={os.getenv("TERA_COOKIE", "")}'
                }
                
                async with session.get(url, headers=headers, allow_redirects=True, timeout=30) as response:
                    html = await response.text()
                    
                    # Look for video player source
                    video_match = re.search(r'"(https?://[^"]+\.mp4[^"]*)"', html)
                    if video_match:
                        video_url = video_match.group(1).replace('\\/', '/')
                        if 'terabox' in video_url or 'd.' in video_url:
                            return {
                                'url': video_url,
                                'filename': 'video.mp4',
                                'filesize': None,
                                'filetype': 'video'
                            }
                    
                    # Look for any download link
                    dlink_match = re.search(r'"dlink"\s*:\s*"([^"]+)"', html)
                    if dlink_match:
                        return {
                            'url': dlink_match.group(1).replace('\\/', '/'),
                            'filename': None,
                            'filesize': None,
                            'filetype': 'file'
                        }
                    
                    return None
                    
        except Exception as e:
            logger.error(f"Direct parsing error: {e}")
            return None
    
    @classmethod
    async def _try_alternative_apis(cls, url: str) -> Optional[Dict[str, Any]]:
        """Try alternative third-party APIs"""
        try:
            async with aiohttp.ClientSession() as session:
                # Try teraboxvideodownloader.pro API
                api_url = "https://teraboxvideodownloader.pro/api/fetch"
                
                headers = {
                    'User-Agent': cls.HEADERS['User-Agent'],
                    'Content-Type': 'application/json',
                    'Origin': 'https://teraboxvideodownloader.pro',
                    'Referer': 'https://teraboxvideodownloader.pro/'
                }
                
                payload = {'url': url}
                
                try:
                    async with session.post(api_url, json=payload, headers=headers, timeout=30) as response:
                        if response.status == 200:
                            data = await response.json()
                            
                            if data.get('success') and data.get('data'):
                                file_data = data['data']
                                download_url = file_data.get('download_url') or file_data.get('dlink')
                                
                                if download_url:
                                    return {
                                        'url': download_url,
                                        'filename': file_data.get('filename') or file_data.get('server_filename'),
                                        'filesize': file_data.get('size'),
                                        'filetype': 'video' if file_data.get('is_video') else 'file'
                                    }
                except Exception as e:
                    logger.debug(f"Third-party API 1 failed: {e}")
                
                # Try another API endpoint
                try:
                    api_url2 = f"https://ytshorts.savetube.me/api/v1/terabox-downloader?url={quote(url)}"
                    
                    async with session.get(api_url2, headers={'User-Agent': cls.HEADERS['User-Agent']}, timeout=30) as response:
                        if response.status == 200:
                            data = await response.json()
                            
                            if data.get('response') and len(data['response']) > 0:
                                file_data = data['response'][0]
                                resolutions = file_data.get('resolutions', {})
                                
                                # Get highest quality
                                for quality in ['HD Video', 'SD Video', 'Fast Download']:
                                    if quality in resolutions:
                                        return {
                                            'url': resolutions[quality],
                                            'filename': file_data.get('title'),
                                            'filesize': None,
                                            'filetype': 'video'
                                        }
                except Exception as e:
                    logger.debug(f"Third-party API 2 failed: {e}")
                
                return None
                
        except Exception as e:
            logger.error(f"Alternative API error: {e}")
            return None


async def extract_via_api(url: str) -> Optional[Dict[str, Any]]:
    """
    Extract download URL using multiple methods
    """
    logger.info(f"[API Layer] Starting extraction: {url}")
    return await TeraboxExtractor.extract(url)
