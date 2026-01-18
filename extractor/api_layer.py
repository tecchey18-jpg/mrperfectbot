"""
Terabox Direct API Extractor
Uses Terabox API directly without heavy browser automation
"""

import asyncio
import aiohttp
import re
import json
import logging
from typing import Optional, Dict, Any, Tuple
from urllib.parse import urlparse, parse_qs, urlencode

logger = logging.getLogger(__name__)


class TeraboxAPI:
    """
    Direct API client for Terabox
    This approach is faster and more reliable than browser automation
    """
    
    BASE_URL = "https://www.terabox.com"
    APP_ID = "250528"
    
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Origin': 'https://www.terabox.com',
        'Referer': 'https://www.terabox.com/',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
    }
    
    @classmethod
    def extract_surl(cls, url: str) -> Optional[str]:
        """Extract surl/shorturl from Terabox URL"""
        # Pattern: /s/1XXXXXX or /s/XXXXXX
        match = re.search(r'/s/1?([a-zA-Z0-9_-]+)', url)
        if match:
            full_match = match.group(0)
            # Check if URL has /s/1XXX format
            if '/s/1' in url:
                return match.group(1)
            return match.group(1)
        
        # Try query param
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        if 'surl' in params:
            return params['surl'][0]
        
        return None
    
    @classmethod
    async def get_file_info(cls, url: str) -> Optional[Dict[str, Any]]:
        """
        Get file information from Terabox share link
        """
        surl = cls.extract_surl(url)
        if not surl:
            logger.error("Could not extract surl from URL")
            return None
        
        logger.info(f"Extracted surl: {surl}")
        
        async with aiohttp.ClientSession() as session:
            try:
                # Step 1: Get the share page to extract jsToken and cookies
                page_data = await cls._get_page_data(session, surl, url)
                if not page_data:
                    return None
                
                js_token = page_data.get('jsToken')
                cookies = page_data.get('cookies', {})
                
                logger.info(f"Got jsToken: {'yes' if js_token else 'no'}")
                
                # Step 2: Get file list
                file_list = await cls._get_file_list(session, surl, js_token, cookies)
                if not file_list:
                    return None
                
                # Step 3: Get download link for the best file
                best_file = cls._select_best_file(file_list)
                if not best_file:
                    return None
                
                logger.info(f"Selected file: {best_file.get('server_filename')}")
                
                # Step 4: Get download link
                download_url = await cls._get_download_link(
                    session, surl, js_token, cookies,
                    best_file.get('fs_id'),
                    page_data.get('uk'),
                    page_data.get('shareid')
                )
                
                if download_url:
                    return {
                        'url': download_url,
                        'filename': best_file.get('server_filename'),
                        'filesize': best_file.get('size'),
                        'filetype': 'video' if best_file.get('category') == 1 else 'file'
                    }
                
                # Fallback: Try dlink from file list
                dlink = best_file.get('dlink')
                if dlink:
                    return {
                        'url': dlink,
                        'filename': best_file.get('server_filename'),
                        'filesize': best_file.get('size'),
                        'filetype': 'video' if best_file.get('category') == 1 else 'file'
                    }
                
                return None
                
            except Exception as e:
                logger.error(f"API extraction error: {e}")
                return None
    
    @classmethod
    async def _get_page_data(cls, session: aiohttp.ClientSession, surl: str, original_url: str) -> Optional[Dict]:
        """Fetch the share page and extract tokens"""
        try:
            # Visit the share page
            share_url = f"{cls.BASE_URL}/sharing/link?surl={surl}"
            
            async with session.get(share_url, headers=cls.HEADERS, allow_redirects=True) as response:
                if response.status != 200:
                    logger.warning(f"Page returned status {response.status}")
                    return None
                
                text = await response.text()
                cookies = {c.key: c.value for c in response.cookies.values()}
                
                # Extract jsToken
                js_token = None
                patterns = [
                    r'window\.jsToken\s*=\s*["\']([^"\']+)["\']',
                    r'"jsToken"\s*:\s*"([^"]+)"',
                    r'jsToken%22%3A%22([^%]+)',
                ]
                for pattern in patterns:
                    match = re.search(pattern, text)
                    if match:
                        js_token = match.group(1)
                        break
                
                # Extract other data
                uk_match = re.search(r'"uk"\s*:\s*(\d+)', text)
                shareid_match = re.search(r'"shareid"\s*:\s*(\d+)', text)
                
                # Try to find data in JSON blob
                try:
                    data_match = re.search(r'window\.yunData\s*=\s*(\{[^;]+\});', text)
                    if data_match:
                        yun_data = json.loads(data_match.group(1))
                        return {
                            'jsToken': js_token,
                            'cookies': cookies,
                            'uk': yun_data.get('uk'),
                            'shareid': yun_data.get('shareid'),
                            'fileList': yun_data.get('file_list', {}).get('list', [])
                        }
                except:
                    pass
                
                return {
                    'jsToken': js_token,
                    'cookies': cookies,
                    'uk': uk_match.group(1) if uk_match else None,
                    'shareid': shareid_match.group(1) if shareid_match else None
                }
                
        except Exception as e:
            logger.error(f"Error getting page data: {e}")
            return None
    
    @classmethod
    async def _get_file_list(cls, session: aiohttp.ClientSession, surl: str, js_token: str, cookies: dict) -> Optional[list]:
        """Get file list from share"""
        try:
            params = {
                'app_id': cls.APP_ID,
                'web': '1',
                'channel': 'dubox',
                'jsToken': js_token or '',
                'page': '1',
                'num': '100',
                'by': 'name',
                'order': 'asc',
                'shorturl': surl,
                'root': '1'
            }
            
            url = f"{cls.BASE_URL}/share/list?" + urlencode(params)
            
            async with session.get(url, headers=cls.HEADERS, cookies=cookies) as response:
                data = await response.json()
                
                if data.get('errno') == 0:
                    file_list = data.get('list', [])
                    logger.info(f"Got {len(file_list)} files from API")
                    return file_list
                else:
                    logger.warning(f"File list API error: {data}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error getting file list: {e}")
            return None
    
    @classmethod
    def _select_best_file(cls, file_list: list) -> Optional[Dict]:
        """Select the best file (prefer videos, then largest)"""
        if not file_list:
            return None
        
        # Handle folders - might need to enter them
        files = [f for f in file_list if f.get('isdir') == 0]
        
        if not files:
            # Check if there are folders we need to enter
            folders = [f for f in file_list if f.get('isdir') == 1]
            if folders:
                logger.warning("Found folders but no direct files")
            return None
        
        # Prefer videos (category 1)
        videos = [f for f in files if f.get('category') == 1]
        if videos:
            return max(videos, key=lambda x: x.get('size', 0))
        
        # Return largest file
        return max(files, key=lambda x: x.get('size', 0))
    
    @classmethod
    async def _get_download_link(
        cls, 
        session: aiohttp.ClientSession, 
        surl: str, 
        js_token: str,
        cookies: dict,
        fs_id: str,
        uk: str,
        shareid: str
    ) -> Optional[str]:
        """Get direct download link"""
        try:
            if not all([fs_id, uk, shareid]):
                logger.warning("Missing required params for download link")
                return None
            
            params = {
                'app_id': cls.APP_ID,
                'web': '1',
                'channel': 'dubox',
                'jsToken': js_token or '',
                'shorturl': surl,
                'fid_list': f'[{fs_id}]',
                'uk': uk,
                'shareid': shareid
            }
            
            url = f"{cls.BASE_URL}/share/download?" + urlencode(params)
            
            async with session.get(url, headers=cls.HEADERS, cookies=cookies) as response:
                data = await response.json()
                
                if data.get('errno') == 0:
                    dlink = data.get('dlink')
                    if dlink:
                        return dlink
                    
                    # Try list format
                    link_list = data.get('list', [])
                    if link_list and link_list[0].get('dlink'):
                        return link_list[0]['dlink']
                
                logger.warning(f"Download API response: {data}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting download link: {e}")
            return None


async def extract_via_api(url: str) -> Optional[Dict[str, Any]]:
    """
    Extract download URL using direct API calls
    This is the fastest and most reliable method
    """
    logger.info(f"[API Layer] Extracting via direct API: {url}")
    return await TeraboxAPI.get_file_info(url)
