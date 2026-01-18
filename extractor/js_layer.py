"""
JavaScript Layer Extraction (Layer 2)
Inspects JavaScript state for embedded download URLs
"""

import asyncio
import json
import re
import logging
from typing import Optional, Dict, Any, List

from playwright.async_api import Page

from .validators import FileValidator
from config import config

logger = logging.getLogger(__name__)


class JSLayer:
    """
    Layer 2: JavaScript State Inspection
    Extracts URLs from window variables, JSON blobs, and player objects
    """
    
    # Common variable patterns that might contain URLs
    WINDOW_VARS = [
        'window.fileInfo',
        'window.yunData',
        'window.locals',
        'window.pageData',
        'window.shareData',
        'window.videoData',
        'window.playerConfig',
        'window.downloadInfo',
        'window.fileList',
        'window.__INITIAL_STATE__',
        'window.__NUXT__',
        'window.__NEXT_DATA__',
        'window.g_config',
        'window.g_data',
        'window.context',
        'window.data',
        'window.share_info',
        'window.file_info',
        'window.video_info',
    ]
    
    @classmethod
    async def extract_window_variables(cls, page: Page) -> List[Dict[str, Any]]:
        """Extract potential file info from window variables"""
        results = []
        
        for var_path in cls.WINDOW_VARS:
            try:
                value = await page.evaluate(f'''
                    () => {{
                        try {{
                            const val = {var_path};
                            return val ? JSON.stringify(val) : null;
                        }} catch(e) {{
                            return null;
                        }}
                    }}
                ''')
                
                if value:
                    try:
                        parsed = json.loads(value)
                        urls = cls._find_urls_in_object(parsed)
                        for url in urls:
                            if FileValidator.is_valid_download_url(url):
                                results.append({
                                    'source': var_path,
                                    'url': url,
                                    'data': parsed
                                })
                    except json.JSONDecodeError:
                        pass
                        
            except Exception as e:
                logger.debug(f"Error checking {var_path}: {e}")
        
        return results
    
    @classmethod
    async def extract_script_json(cls, page: Page) -> List[Dict[str, Any]]:
        """Extract JSON data from inline script tags"""
        results = []
        
        script_contents = await page.evaluate('''
            () => {
                const scripts = Array.from(document.querySelectorAll('script:not([src])'));
                return scripts.map(s => s.textContent).filter(Boolean);
            }
        ''')
        
        for content in script_contents:
            # Look for JSON object patterns
            json_patterns = [
                r'var\s+\w+\s*=\s*(\{[^;]+\});',
                r'"dlink"\s*:\s*"([^"]+)"',
                r'"downloadUrl"\s*:\s*"([^"]+)"',
                r'"download_url"\s*:\s*"([^"]+)"',
                r'"file_url"\s*:\s*"([^"]+)"',
                r'"play_url"\s*:\s*"([^"]+)"',
                r'"stream_url"\s*:\s*"([^"]+)"',
                r'"video_url"\s*:\s*"([^"]+)"',
                r'"hls_url"\s*:\s*"([^"]+)"',
                r'"src"\s*:\s*"(https?://[^"]+terabox[^"]+)"',
            ]
            
            for pattern in json_patterns:
                matches = re.findall(pattern, content, re.DOTALL)
                for match in matches:
                    if isinstance(match, str):
                        # Direct URL pattern
                        url = match.replace('\\/', '/')
                        if FileValidator.is_valid_download_url(url):
                            results.append({
                                'source': 'script_regex',
                                'url': url
                            })
                    else:
                        # JSON object
                        try:
                            parsed = json.loads(match)
                            urls = cls._find_urls_in_object(parsed)
                            for url in urls:
                                if FileValidator.is_valid_download_url(url):
                                    results.append({
                                        'source': 'script_json',
                                        'url': url,
                                        'data': parsed
                                    })
                        except json.JSONDecodeError:
                            pass
        
        return results
    
    @classmethod
    async def extract_player_objects(cls, page: Page) -> List[Dict[str, Any]]:
        """Look for video player objects that might have URLs"""
        results = []
        
        player_script = '''
            () => {
                const sources = [];
                
                // Check video elements
                const videos = document.querySelectorAll('video');
                videos.forEach(v => {
                    if (v.src) sources.push({ type: 'video_src', url: v.src });
                    const videoSources = v.querySelectorAll('source');
                    videoSources.forEach(s => {
                        if (s.src) sources.push({ type: 'source_src', url: s.src });
                    });
                });
                
                // Check common player libraries
                const playerVars = [
                    'jwplayer', 'videojs', 'Artplayer', 'DPlayer',
                    'Plyr', 'MediaElement', 'Flowplayer'
                ];
                
                playerVars.forEach(name => {
                    try {
                        if (window[name]) {
                            const player = window[name];
                            // Try to get source from player
                            if (typeof player.getPlaylist === 'function') {
                                const playlist = player.getPlaylist();
                                if (playlist && playlist.length) {
                                    playlist.forEach(item => {
                                        if (item.file) sources.push({ type: name + '_playlist', url: item.file });
                                        if (item.sources) {
                                            item.sources.forEach(s => {
                                                if (s.file) sources.push({ type: name + '_source', url: s.file });
                                            });
                                        }
                                    });
                                }
                            }
                        }
                    } catch(e) {}
                });
                
                return sources;
            }
        '''
        
        try:
            sources = await page.evaluate(player_script)
            for source in sources:
                url = source.get('url', '')
                if FileValidator.is_valid_download_url(url):
                    results.append({
                        'source': source.get('type', 'player'),
                        'url': url
                    })
        except Exception as e:
            logger.debug(f"Error extracting player objects: {e}")
        
        return results
    
    @classmethod
    def _find_urls_in_object(cls, obj: Any, depth: int = 0) -> List[str]:
        """Recursively find URLs in a JSON object"""
        urls = []
        
        if depth > 10:  # Prevent infinite recursion
            return urls
        
        if isinstance(obj, str):
            # Check if it's a URL
            if obj.startswith('http') and ('terabox' in obj.lower() or FileValidator.is_cdn_url(obj)):
                urls.append(obj.replace('\\/', '/'))
        
        elif isinstance(obj, dict):
            # Check known URL keys
            url_keys = [
                'dlink', 'download', 'downloadUrl', 'download_url',
                'url', 'src', 'file', 'path', 'link', 'stream',
                'playUrl', 'play_url', 'video_url', 'file_url',
                'hls', 'hlsUrl', 'hls_url', 'm3u8', 'mp4'
            ]
            
            for key in url_keys:
                if key in obj:
                    val = obj[key]
                    if isinstance(val, str) and val.startswith('http'):
                        urls.append(val.replace('\\/', '/'))
                    elif isinstance(val, list):
                        for item in val:
                            if isinstance(item, str) and item.startswith('http'):
                                urls.append(item.replace('\\/', '/'))
                            elif isinstance(item, dict):
                                urls.extend(cls._find_urls_in_object(item, depth + 1))
            
            # Recurse into dict values
            for value in obj.values():
                urls.extend(cls._find_urls_in_object(value, depth + 1))
        
        elif isinstance(obj, list):
            for item in obj:
                urls.extend(cls._find_urls_in_object(item, depth + 1))
        
        return urls


async def extract_via_js(page: Page) -> Optional[Dict[str, Any]]:
    """
    Extract download URL by inspecting JavaScript state
    
    Args:
        page: Playwright page (already navigated)
    
    Returns:
        Dictionary with download info or None
    """
    logger.info("[JS Layer] Inspecting JavaScript state...")
    
    all_results = []
    
    try:
        # Try window variables
        window_results = await JSLayer.extract_window_variables(page)
        all_results.extend(window_results)
        
        # Try script JSON
        script_results = await JSLayer.extract_script_json(page)
        all_results.extend(script_results)
        
        # Try player objects
        player_results = await JSLayer.extract_player_objects(page)
        all_results.extend(player_results)
        
        if all_results:
            # Return the first valid result
            best = all_results[0]
            logger.info(f"[JS Layer] Found URL from {best.get('source')}")
            
            return {
                'url': best['url'],
                'source': best.get('source'),
                'filename': None,  # May extract from data if available
                'filesize': None,
                'filetype': 'video'  # Assume video for JS layer
            }
        
        logger.info("[JS Layer] No download URL found in JavaScript state")
        return None
    
    except Exception as e:
        logger.error(f"[JS Layer] Error: {e}")
        return None
