"""
Dynamic Fingerprint Generation
Generates realistic, randomized browser fingerprints per session
Each fingerprint is internally consistent across all properties
"""

import random
import hashlib
import secrets
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple


@dataclass
class Fingerprint:
    """Complete browser fingerprint configuration"""
    user_agent: str
    viewport: Dict[str, int]
    screen: Dict[str, int]
    timezone: str
    locale: str
    languages: List[str]
    platform: str
    device_memory: int
    hardware_concurrency: int
    webgl_vendor: str
    webgl_renderer: str
    color_depth: int
    pixel_ratio: float
    do_not_track: Optional[str]
    touch_support: Dict[str, Any]
    client_hints: Dict[str, Any]
    
    # Audio fingerprint seed
    audio_context_seed: float = 0.0
    
    # Canvas fingerprint seed
    canvas_seed: int = 0
    
    # Font list
    fonts: List[str] = field(default_factory=list)
    
    # Battery
    battery: Dict[str, Any] = field(default_factory=dict)
    
    # Connection info
    connection: Dict[str, Any] = field(default_factory=dict)
    
    def to_context_options(self) -> Dict[str, Any]:
        """Convert to Playwright context options"""
        return {
            'user_agent': self.user_agent,
            'viewport': self.viewport,
            'screen': self.screen,
            'timezone_id': self.timezone,
            'locale': self.locale,
            'color_scheme': 'light',
            'device_scale_factor': self.pixel_ratio,
            'is_mobile': False,
            'has_touch': self.touch_support['maxTouchPoints'] > 0,
            'extra_http_headers': self._build_headers(),
        }
    
    def _build_headers(self) -> Dict[str, str]:
        """Build realistic HTTP headers including client hints"""
        headers = {
            'Accept-Language': ','.join(f'{lang};q={1.0 - i * 0.1:.1f}' for i, lang in enumerate(self.languages[:3])),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-User': '?1',
            'Sec-Fetch-Dest': 'document',
            'Cache-Control': 'max-age=0',
        }
        
        # Add client hints (Chrome 130+)
        if self.client_hints:
            for key, value in self.client_hints.items():
                header_key = key.replace('_', '-')
                if header_key.startswith('sec-ch-'):
                    # Proper header case
                    headers[header_key] = str(value)
        
        return headers


class FingerprintGenerator:
    """
    Generates realistic browser fingerprints
    Each fingerprint is unique but internally consistent
    All values correlate properly (e.g., GPU matches platform)
    """
    
    # Chrome versions (late 2025 - 2026 range)
    CHROME_VERSIONS: List[Tuple[str, str]] = [
        ('124', '124.0.6367.91'),
        ('125', '125.0.6422.60'),
        ('126', '126.0.6478.55'),
        ('127', '127.0.6533.72'),
        ('128', '128.0.6613.84'),
        ('129', '129.0.6668.42'),
        ('130', '130.0.6723.91'),
        ('131', '131.0.6778.85'),
        ('132', '132.0.6834.57'),
    ]
    
    # Windows versions
    WINDOWS_VERSIONS: List[Tuple[str, str, str]] = [
        ('10.0', 'Windows NT 10.0; Win64; x64', '10.0.0'),
        ('11.0', 'Windows NT 10.0; Win64; x64', '15.0.0'),  # Win11 reports as 10.0
    ]
    
    # Mac OS versions
    MACOS_VERSIONS: List[Tuple[str, str, str]] = [
        ('10_15_7', 'Macintosh; Intel Mac OS X 10_15_7', '10.15.7'),
        ('12_7_1', 'Macintosh; Intel Mac OS X 12_7_1', '12.7.1'),
        ('13_6_3', 'Macintosh; Intel Mac OS X 13_6_3', '13.6.3'),
        ('14_2_1', 'Macintosh; Intel Mac OS X 14_2_1', '14.2.1'),
        ('14_5', 'Macintosh; Intel Mac OS X 14_5', '14.5'),
    ]
    
    # Viewport configurations (common desktop resolutions)
    VIEWPORTS: List[Dict[str, int]] = [
        {'width': 1920, 'height': 1080},
        {'width': 1536, 'height': 864},
        {'width': 1440, 'height': 900},
        {'width': 1366, 'height': 768},
        {'width': 1280, 'height': 720},
        {'width': 2560, 'height': 1440},
        {'width': 1680, 'height': 1050},
        {'width': 1600, 'height': 900},
        {'width': 1920, 'height': 1200},
        {'width': 1280, 'height': 800},
    ]
    
    # Timezones weighted by population centers
    TIMEZONES: List[Tuple[str, List[str], str, float]] = [
        ('America/New_York', ['en-US', 'en'], 'en-US', 0.12),
        ('America/Los_Angeles', ['en-US', 'en'], 'en-US', 0.10),
        ('America/Chicago', ['en-US', 'en'], 'en-US', 0.06),
        ('Europe/London', ['en-GB', 'en'], 'en-GB', 0.08),
        ('Europe/Paris', ['fr-FR', 'fr', 'en'], 'fr-FR', 0.04),
        ('Europe/Berlin', ['de-DE', 'de', 'en'], 'de-DE', 0.05),
        ('Asia/Tokyo', ['ja-JP', 'ja', 'en'], 'ja-JP', 0.04),
        ('Asia/Shanghai', ['zh-CN', 'zh', 'en'], 'zh-CN', 0.06),
        ('Asia/Kolkata', ['en-IN', 'hi-IN', 'en'], 'en-IN', 0.15),
        ('Asia/Singapore', ['en-SG', 'zh-SG', 'en'], 'en-SG', 0.03),
        ('Australia/Sydney', ['en-AU', 'en'], 'en-AU', 0.03),
        ('Europe/Moscow', ['ru-RU', 'ru', 'en'], 'ru-RU', 0.03),
        ('America/Sao_Paulo', ['pt-BR', 'pt', 'en'], 'pt-BR', 0.04),
        ('Asia/Seoul', ['ko-KR', 'ko', 'en'], 'ko-KR', 0.03),
        ('Asia/Dubai', ['ar-AE', 'en-AE', 'en'], 'ar-AE', 0.02),
        ('Asia/Jakarta', ['id-ID', 'id', 'en'], 'id-ID', 0.05),
        ('Europe/Amsterdam', ['nl-NL', 'nl', 'en'], 'nl-NL', 0.02),
        ('Asia/Manila', ['en-PH', 'fil-PH', 'en'], 'en-PH', 0.05),
    ]
    
    # WebGL configurations - must match platform expectations
    WEBGL_CONFIGS_WINDOWS: List[Tuple[str, str]] = [
        ('Google Inc. (NVIDIA)', 'ANGLE (NVIDIA, NVIDIA GeForce RTX 3060 Direct3D11 vs_5_0 ps_5_0, D3D11)'),
        ('Google Inc. (NVIDIA)', 'ANGLE (NVIDIA, NVIDIA GeForce RTX 3070 Direct3D11 vs_5_0 ps_5_0, D3D11)'),
        ('Google Inc. (NVIDIA)', 'ANGLE (NVIDIA, NVIDIA GeForce RTX 4060 Direct3D11 vs_5_0 ps_5_0, D3D11)'),
        ('Google Inc. (NVIDIA)', 'ANGLE (NVIDIA, NVIDIA GeForce RTX 4070 Direct3D11 vs_5_0 ps_5_0, D3D11)'),
        ('Google Inc. (NVIDIA)', 'ANGLE (NVIDIA, NVIDIA GeForce GTX 1660 Super Direct3D11 vs_5_0 ps_5_0, D3D11)'),
        ('Google Inc. (AMD)', 'ANGLE (AMD, AMD Radeon RX 6700 XT Direct3D11 vs_5_0 ps_5_0, D3D11)'),
        ('Google Inc. (AMD)', 'ANGLE (AMD, AMD Radeon RX 7600 Direct3D11 vs_5_0 ps_5_0, D3D11)'),
        ('Google Inc. (Intel)', 'ANGLE (Intel, Intel(R) UHD Graphics 770 Direct3D11 vs_5_0 ps_5_0, D3D11)'),
        ('Google Inc. (Intel)', 'ANGLE (Intel, Intel(R) Iris(R) Xe Graphics Direct3D11 vs_5_0 ps_5_0, D3D11)'),
    ]
    
    WEBGL_CONFIGS_MAC: List[Tuple[str, str]] = [
        ('Apple Inc.', 'Apple M1'),
        ('Apple Inc.', 'Apple M1 Pro'),
        ('Apple Inc.', 'Apple M2'),
        ('Apple Inc.', 'Apple M2 Pro'),
        ('Apple Inc.', 'Apple M3'),
        ('Apple Inc.', 'Apple M3 Pro'),
        ('Apple Inc.', 'AMD Radeon Pro 5500M OpenGL Engine'),
        ('Apple Inc.', 'Intel(R) Iris(TM) Plus Graphics OpenGL Engine'),
    ]
    
    # Common system fonts
    COMMON_FONTS: List[str] = [
        'Arial', 'Arial Black', 'Calibri', 'Cambria', 'Comic Sans MS',
        'Consolas', 'Courier New', 'Georgia', 'Helvetica', 'Impact',
        'Lucida Console', 'Lucida Sans Unicode', 'Microsoft Sans Serif',
        'Palatino Linotype', 'Segoe UI', 'Tahoma', 'Times New Roman',
        'Trebuchet MS', 'Verdana', 'Webdings', 'Wingdings'
    ]
    
    MAC_FONTS: List[str] = [
        'Helvetica Neue', 'Menlo', 'Monaco', 'San Francisco', 'SF Pro',
        'Avenir', 'Avenir Next', 'Futura', 'Gill Sans', 'Optima'
    ]
    
    @classmethod
    def generate(cls, seed: Optional[str] = None) -> Fingerprint:
        """
        Generate a complete, consistent fingerprint
        
        Args:
            seed: Optional seed for reproducibility
        
        Returns:
            Fingerprint object with all properties
        """
        if seed:
            random.seed(hashlib.sha256(seed.encode()).hexdigest())
        else:
            random.seed(secrets.token_hex(32))
        
        # Select OS (weighted - more Windows users)
        os_type = random.choices(['windows', 'macos'], weights=[0.75, 0.25])[0]
        
        if os_type == 'windows':
            os_version_tuple = random.choice(cls.WINDOWS_VERSIONS)
            os_string = os_version_tuple[1]
            platform_version = os_version_tuple[2]
            platform = 'Win32'
            webgl_config = random.choice(cls.WEBGL_CONFIGS_WINDOWS)
            fonts = cls.COMMON_FONTS.copy()
        else:
            os_version_tuple = random.choice(cls.MACOS_VERSIONS)
            os_string = os_version_tuple[1]
            platform_version = os_version_tuple[2]
            platform = 'MacIntel'
            webgl_config = random.choice(cls.WEBGL_CONFIGS_MAC)
            fonts = cls.COMMON_FONTS + cls.MAC_FONTS
        
        # Randomize font list
        random.shuffle(fonts)
        fonts = fonts[:random.randint(15, len(fonts))]
        
        # Select Chrome version
        chrome_major, chrome_full = random.choice(cls.CHROME_VERSIONS)
        
        # Build User-Agent
        user_agent = f'Mozilla/5.0 ({os_string}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_full} Safari/537.36'
        
        # Select viewport and screen
        viewport = random.choice(cls.VIEWPORTS).copy()
        
        # Screen is slightly larger than viewport (taskbar, etc.)
        screen = {
            'width': viewport['width'],
            'height': viewport['height'] + random.choice([0, 40, 48, 56])  # Taskbar heights
        }
        
        # Select timezone with weighted random
        weights = [tz[3] for tz in cls.TIMEZONES]
        timezone_data = random.choices(cls.TIMEZONES, weights=weights)[0]
        timezone = timezone_data[0]
        languages = timezone_data[1].copy()
        locale = timezone_data[2]
        
        # Hardware specs (realistic correlations)
        device_memory = random.choice([4, 8, 8, 16, 16, 32])  # Weighted towards 8-16GB
        hardware_concurrency = random.choice([4, 6, 8, 8, 12, 16])  # Common core counts
        
        # Pixel ratio (most common values)
        pixel_ratio = random.choice([1.0, 1.0, 1.25, 1.25, 1.5, 2.0])
        
        # Touch support (desktop = no touch usually)
        touch_support = {
            'maxTouchPoints': 0,
            'ontouchstart': False,
            'ontouchend': False
        }
        
        # Client hints for Chrome
        client_hints = cls._generate_client_hints(
            chrome_major, chrome_full, platform, platform_version, os_type
        )
        
        # Audio and canvas seeds for consistent fingerprinting
        audio_context_seed = random.random()
        canvas_seed = random.randint(0, 2**31 - 1)
        
        # Battery (randomized but realistic)
        battery = {
            'charging': random.choice([True, True, True, False]),  # Usually plugged in
            'chargingTime': random.choice([0, float('inf')]),
            'dischargingTime': random.randint(3600, 28800) if not random.choice([True, False]) else float('inf'),
            'level': round(random.uniform(0.3, 1.0), 2)
        }
        
        # Connection info
        connection = {
            'effectiveType': random.choice(['4g', '4g', '4g', '3g']),
            'downlink': random.choice([10, 10, 5.65, 2.8, 1.4]),
            'rtt': random.choice([50, 100, 150, 200]),
            'saveData': False
        }
        
        return Fingerprint(
            user_agent=user_agent,
            viewport=viewport,
            screen=screen,
            timezone=timezone,
            locale=locale,
            languages=languages,
            platform=platform,
            device_memory=device_memory,
            hardware_concurrency=hardware_concurrency,
            webgl_vendor=webgl_config[0],
            webgl_renderer=webgl_config[1],
            color_depth=24,
            pixel_ratio=pixel_ratio,
            do_not_track=random.choice([None, '1', None, None]),  # Most don't have DNT
            touch_support=touch_support,
            client_hints=client_hints,
            audio_context_seed=audio_context_seed,
            canvas_seed=canvas_seed,
            fonts=fonts,
            battery=battery,
            connection=connection
        )
    
    @classmethod
    def _generate_client_hints(
        cls,
        chrome_major: str,
        chrome_full: str,
        platform: str,
        platform_version: str,
        os_type: str
    ) -> Dict[str, Any]:
        """Generate Chrome Client Hints headers"""
        brands = [
            f'"Chromium";v="{chrome_major}"',
            f'"Google Chrome";v="{chrome_major}"',
            '"Not=A?Brand";v="99"'
        ]
        random.shuffle(brands)
        
        platform_name = 'Windows' if os_type == 'windows' else 'macOS'
        
        return {
            'sec-ch-ua': ', '.join(brands),
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': f'"{platform_name}"',
            'sec-ch-ua-platform-version': f'"{platform_version}"',
            'sec-ch-ua-arch': '"x86"',
            'sec-ch-ua-bitness': '"64"',
            'sec-ch-ua-model': '""',
            'sec-ch-ua-full-version-list': f'"Chromium";v="{chrome_full}", "Google Chrome";v="{chrome_full}", "Not=A?Brand";v="99.0.0.0"'
        }
