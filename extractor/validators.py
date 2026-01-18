"""
URL and File Validators
Validates Terabox URLs and extracted content
"""

import re
import logging
from typing import Optional, Tuple, List
from urllib.parse import urlparse, parse_qs

from config import config

logger = logging.getLogger(__name__)


class URLValidator:
    """Validates Terabox URLs and domains"""
    
    @classmethod
    def is_valid_terabox_url(cls, url: str) -> bool:
        """Check if URL is from a supported Terabox domain"""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            
            # Remove www. prefix
            if domain.startswith('www.'):
                domain = domain[4:]
            
            # Check against supported domains
            for supported in config.extraction.supported_domains:
                if domain == supported or domain.endswith('.' + supported):
                    return True
            
            return False
        except Exception as e:
            logger.error(f"Error validating URL: {e}")
            return False
    
    @classmethod
    def normalize_url(cls, url: str) -> str:
        """Normalize URL for processing"""
        url = url.strip()
        
        # Add protocol if missing
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        return url
    
    @classmethod
    def extract_share_id(cls, url: str) -> Optional[str]:
        """Extract share ID from Terabox URL"""
        try:
            parsed = urlparse(url)
            
            # Check path for /s/ pattern
            path_match = re.search(r'/s/([a-zA-Z0-9_-]+)', parsed.path)
            if path_match:
                return path_match.group(1)
            
            # Check query params
            params = parse_qs(parsed.query)
            if 'surl' in params:
                return params['surl'][0]
            
            return None
        except Exception as e:
            logger.error(f"Error extracting share ID: {e}")
            return None


class FileValidator:
    """Validates extracted download URLs and file information"""
    
    # Video MIME types
    VIDEO_MIMES = {
        'video/mp4', 'video/webm', 'video/avi', 'video/mkv',
        'video/x-matroska', 'video/quicktime', 'video/x-msvideo',
        'video/x-flv', 'video/3gpp', 'video/mpeg'
    }
    
    # Document/archive MIME types
    DOCUMENT_MIMES = {
        'application/pdf', 'application/zip', 'application/x-rar-compressed',
        'application/x-7z-compressed', 'application/x-tar',
        'application/gzip', 'application/octet-stream'
    }
    
    # Audio MIME types
    AUDIO_MIMES = {
        'audio/mpeg', 'audio/mp3', 'audio/wav', 'audio/aac',
        'audio/ogg', 'audio/flac', 'audio/x-m4a'
    }
    
    @classmethod
    def is_cdn_url(cls, url: str) -> bool:
        """Check if URL matches known CDN patterns"""
        try:
            parsed = urlparse(url)
            host = parsed.netloc.lower()
            
            for pattern in config.extraction.cdn_patterns:
                if pattern in host:
                    return True
            
            return False
        except Exception:
            return False
    
    @classmethod
    def has_signature_params(cls, url: str) -> bool:
        """Check if URL has signed query parameters"""
        try:
            parsed = urlparse(url)
            params = parse_qs(parsed.query)
            
            for signature_param in config.extraction.signature_params:
                if signature_param in params:
                    return True
            
            return False
        except Exception:
            return False
    
    @classmethod
    def is_valid_download_url(cls, url: str) -> bool:
        """
        Validate if URL is likely a valid download URL
        Checks CDN patterns and signature parameters
        """
        return cls.is_cdn_url(url) and cls.has_signature_params(url)
    
    @classmethod
    def get_file_type(cls, content_type: Optional[str]) -> str:
        """Determine file type from content-type header"""
        if not content_type:
            return 'unknown'
        
        content_type = content_type.lower().split(';')[0].strip()
        
        if content_type in cls.VIDEO_MIMES:
            return 'video'
        elif content_type in cls.AUDIO_MIMES:
            return 'audio'
        elif content_type in cls.DOCUMENT_MIMES:
            return 'document'
        elif content_type.startswith('image/'):
            return 'image'
        else:
            return 'file'
    
    @classmethod
    def parse_content_disposition(cls, header: str) -> Optional[str]:
        """Extract filename from Content-Disposition header"""
        if not header:
            return None
        
        # Try filename*= (RFC 5987) first
        match = re.search(r"filename\*=(?:UTF-8''|utf-8'')(.+?)(?:;|$)", header, re.I)
        if match:
            from urllib.parse import unquote
            return unquote(match.group(1))
        
        # Try filename=
        match = re.search(r'filename="?([^";\n]+)"?', header, re.I)
        if match:
            return match.group(1).strip()
        
        return None
    
    @classmethod
    def parse_content_length(cls, header: str) -> Optional[int]:
        """Parse Content-Length header value"""
        if not header:
            return None
        
        try:
            return int(header)
        except (ValueError, TypeError):
            return None
    
    @classmethod
    def format_file_size(cls, size_bytes: Optional[int]) -> str:
        """Format file size for display"""
        if size_bytes is None:
            return "Unknown size"
        
        units = ['B', 'KB', 'MB', 'GB', 'TB']
        size = float(size_bytes)
        
        for unit in units[:-1]:
            if abs(size) < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0
        
        return f"{size:.2f} {units[-1]}"
    
    @classmethod
    def validate_extracted_url(cls, url: str, content_length: Optional[int]) -> Tuple[bool, str]:
        """
        Full validation of extracted URL
        
        Returns:
            Tuple of (is_valid, reason)
        """
        if not url:
            return False, "Empty URL"
        
        if not url.startswith('http'):
            return False, "Invalid protocol"
        
        if not cls.is_cdn_url(url):
            return False, "Not a CDN URL"
        
        if not cls.has_signature_params(url):
            return False, "Missing signature parameters"
        
        if content_length is not None and content_length < config.extraction.min_file_size:
            return False, f"File too small ({cls.format_file_size(content_length)})"
        
        return True, "Valid"
