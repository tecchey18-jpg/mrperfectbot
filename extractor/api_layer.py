"""
Terabox Direct API Extractor
Uses Terabox API with ndus cookie authentication (like working bots)
"""

import asyncio
import aiohttp
import re
import json
import logging
from typing import Optional, Dict, Any, List
from urllib.parse import urlparse, parse_qs, urlencode
import os

logger = logging.getLogger(__name__)


class TeraboxAPI:
    """
    Direct API client for Terabox
    Uses ndus cookie authentication like TeraBoxFastDLBot
    """
    
    # Supported domains
    DOMAINS = [
        'terabox.com', '1024tera.com', 'teraboxapp.com', '4funbox.com',
        'mirrobox.com', 'nephobox.com', 'freeterabox.com', 'momerybox.com',
        'teraboxlink.com', 'terasharelink.com', '1024terabox.com'
    ]
    
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
    }
    
    @classmethod
    def get_ndus_cookie(cls) -> str:
        """Get ndus cookie from environment"""
        return os.getenv('TERA_COOKIE', os.getenv('NDUS_COOKIE', ''))
    
    @classmethod
    def extract_surl(cls, url: str) -> Optional[str]:
        """Extract surl/shorturl from Terabox URL"""
        # Pattern: /s/1XXXXXX or /s/XXXXXX
        match = re.search(r'/s/1?([a-zA-Z0-9_-]+)', url)
        if match:
            return match.group(1)
        
        # Try query param
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        if 'surl' in params:
            return params['surl'][0]
        
        return None
    
    @classmethod
    def get_base_url(cls, url: str) -> str:
        """Get base URL from the share link"""
        parsed = urlparse(url)
        for domain in cls.DOMAINS:
            if domain in parsed.netloc:
                return f"https://www.{domain}"
        return "https://www.terabox.com"
    
    @classmethod
    async def get_file_info(cls, url: str) -> Optional[Dict[str, Any]]:
        """
        Get file information from Terabox share link
        Uses ndus cookie authentication
        """
        surl = cls.extract_surl(url)
        if not surl:
            logger.error("Could not extract surl from URL")
            return None
        
        logger.info(f"Extracted surl: {surl}")
        
        ndus = cls.get_ndus_cookie()
        base_url = cls.get_base_url(url)
        
        logger.info(f"Using base URL: {base_url}")
        logger.info(f"NDUS cookie: {'present' if ndus else 'NOT SET'}")
        
        # Set up cookies
        cookies = {}
        if ndus:
            cookies['ndus'] = ndus
        
        async with aiohttp.ClientSession(cookies=cookies) as session:
            try:
                # Step 1: Get the share page HTML to extract data
                share_url = f"{base_url}/sharing/link?surl={surl}"
                logger.info(f"Fetching share page: {share_url}")
                
                async with session.get(share_url, headers=cls.HEADERS, allow_redirects=True) as response:
                    if response.status != 200:
                        logger.warning(f"Page returned status {response.status}")
                        return None
                    
                    html = await response.text()
                    
                    # Update cookies from response
                    for cookie in response.cookies.values():
                        cookies[cookie.key] = cookie.value
                
                # Extract data from HTML
                page_data = cls._extract_page_data(html)
                if not page_data:
                    logger.warning("Could not extract page data")
                    return None
                
                logger.info(f"Found jsToken: {'yes' if page_data.get('jsToken') else 'no'}")
                logger.info(f"Found file list with {len(page_data.get('fileList', []))} files")
                
                # If we already have file list with dlink, use it
                file_list = page_data.get('fileList', [])
                if file_list:
                    for f in file_list:
                        if f.get('dlink'):
                            logger.info("Found dlink in initial page data!")
                            return {
                                'url': f['dlink'],
                                'filename': f.get('server_filename'),
                                'filesize': f.get('size'),
                                'filetype': 'video' if f.get('category') == 1 else 'file'
                            }
                
                # Step 2: Use API to get file list
                js_token = page_data.get('jsToken', '')
                
                list_params = {
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
                
                list_url = f"{base_url}/share/list?" + urlencode(list_params)
                logger.info("Fetching file list via API...")
                
                async with session.get(list_url, headers=cls.HEADERS) as response:
                    data = await response.json()
                    
                    if data.get('errno') != 0:
                        logger.warning(f"File list API error: errno={data.get('errno')}")
                        # Try without jsToken
                        return await cls._try_without_token(session, base_url, surl, cookies)
                    
                    file_list = data.get('list', [])
                    logger.info(f"Got {len(file_list)} files from API")
                    
                    if not file_list:
                        return None
                    
                    # Get the best file
                    best_file = cls._select_best_file(file_list)
                    if not best_file:
                        return None
                    
                    logger.info(f"Selected file: {best_file.get('server_filename')}")
                    
                    # Check if file already has dlink
                    if best_file.get('dlink'):
                        return {
                            'url': best_file['dlink'],
                            'filename': best_file.get('server_filename'),
                            'filesize': best_file.get('size'),
                            'filetype': 'video' if best_file.get('category') == 1 else 'file'
                        }
                    
                    # Step 3: Get download link
                    download_url = await cls._get_download_link(
                        session, base_url, surl, js_token,
                        best_file.get('fs_id'),
                        data.get('uk'),
                        data.get('shareid')
                    )
                    
                    if download_url:
                        return {
                            'url': download_url,
                            'filename': best_file.get('server_filename'),
                            'filesize': best_file.get('size'),
                            'filetype': 'video' if best_file.get('category') == 1 else 'file'
                        }
                    
                    return None
                    
            except Exception as e:
                logger.error(f"API extraction error: {e}", exc_info=True)
                return None
    
    @classmethod
    def _extract_page_data(cls, html: str) -> Optional[Dict]:
        """Extract data from page HTML"""
        result = {}
        
        # Extract jsToken
        patterns = [
            r'window\.jsToken\s*=\s*["\']([^"\']+)["\']',
            r'"jsToken"\s*:\s*"([^"]+)"',
            r"fn%28%22([a-fA-F0-9]+)%22%29",
        ]
        for pattern in patterns:
            match = re.search(pattern, html)
            if match:
                result['jsToken'] = match.group(1)
                break
        
        # Try to extract yunData
        try:
            yun_match = re.search(r'window\.yunData\s*=\s*(\{[^;]+\});', html)
            if yun_match:
                yun_data = json.loads(yun_match.group(1))
                result['yunData'] = yun_data
                result['uk'] = yun_data.get('uk')
                result['shareid'] = yun_data.get('shareid')
                
                file_list = yun_data.get('file_list', {})
                if isinstance(file_list, dict):
                    result['fileList'] = file_list.get('list', [])
                elif isinstance(file_list, list):
                    result['fileList'] = file_list
        except json.JSONDecodeError:
            pass
        
        # Try to extract from __INITIAL_DATA__
        try:
            init_match = re.search(r'window\.__INITIAL_DATA__\s*=\s*(\{.+?\});', html, re.DOTALL)
            if init_match:
                init_data = json.loads(init_match.group(1))
                if 'fileList' not in result:
                    result['fileList'] = init_data.get('file_list', {}).get('list', [])
        except:
            pass
        
        return result if result else None
    
    @classmethod
    def _select_best_file(cls, file_list: list) -> Optional[Dict]:
        """Select the best file (prefer videos, then largest)"""
        if not file_list:
            return None
        
        # Filter out directories
        files = [f for f in file_list if f.get('isdir') == 0 or f.get('isdir') == '0']
        
        if not files:
            # Maybe all are marked differently
            files = [f for f in file_list if not f.get('isdir')]
        
        if not files:
            # Just use all
            files = file_list
        
        # Prefer videos (category 1)
        videos = [f for f in files if f.get('category') == 1]
        if videos:
            return max(videos, key=lambda x: int(x.get('size', 0) or 0))
        
        # Return largest file
        return max(files, key=lambda x: int(x.get('size', 0) or 0))
    
    @classmethod
    async def _get_download_link(
        cls,
        session: aiohttp.ClientSession,
        base_url: str,
        surl: str,
        js_token: str,
        fs_id,
        uk,
        shareid
    ) -> Optional[str]:
        """Get direct download link"""
        try:
            if not all([fs_id, uk, shareid]):
                logger.warning(f"Missing params: fs_id={fs_id}, uk={uk}, shareid={shareid}")
                return None
            
            params = {
                'app_id': '250528',
                'web': '1',
                'channel': 'dubox',
                'jsToken': js_token or '',
                'dp-logid': '',
                'shorturl': surl,
                'fid_list': f'[{fs_id}]',
                'uk': str(uk),
                'shareid': str(shareid),
            }
            
            url = f"{base_url}/share/download?" + urlencode(params)
            logger.info("Fetching download link...")
            
            async with session.get(url, headers=cls.HEADERS) as response:
                data = await response.json()
                
                logger.info(f"Download API response errno: {data.get('errno')}")
                
                if data.get('errno') == 0:
                    # Direct dlink
                    if data.get('dlink'):
                        return data['dlink']
                    
                    # List format
                    if data.get('list') and len(data['list']) > 0:
                        return data['list'][0].get('dlink')
                
                # Try errno -20 which sometimes has link
                if data.get('dlink'):
                    return data['dlink']
                
                logger.warning(f"Download API failed: {data}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting download link: {e}")
            return None
    
    @classmethod
    async def _try_without_token(
        cls,
        session: aiohttp.ClientSession,
        base_url: str,
        surl: str,
        cookies: dict
    ) -> Optional[Dict[str, Any]]:
        """Try alternative extraction without jsToken"""
        logger.info("Trying alternative extraction method...")
        
        try:
            # Try direct API endpoint
            share_info_url = f"{base_url}/api/shareinfo?surl={surl}&app_id=250528&web=1&channel=dubox"
            
            async with session.get(share_info_url, headers=cls.HEADERS) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('errno') == 0:
                        file_list = data.get('list', [])
                        if file_list:
                            best = cls._select_best_file(file_list)
                            if best and best.get('dlink'):
                                return {
                                    'url': best['dlink'],
                                    'filename': best.get('server_filename'),
                                    'filesize': best.get('size'),
                                    'filetype': 'video' if best.get('category') == 1 else 'file'
                                }
        except Exception as e:
            logger.debug(f"Alternative method failed: {e}")
        
        return None


async def extract_via_api(url: str) -> Optional[Dict[str, Any]]:
    """
    Extract download URL using direct API calls
    This is the fastest and most reliable method
    """
    logger.info(f"[API Layer] Extracting via direct API: {url}")
    return await TeraboxAPI.get_file_info(url)
