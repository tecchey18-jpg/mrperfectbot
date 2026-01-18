"""
Message Templates
All bot message strings and formatting
"""

from typing import Optional
from extractor.validators import FileValidator


class Messages:
    """Bot message templates"""
    
    WELCOME = """🚀 <b>Terabox Link Extractor</b>

Welcome! Send me a Terabox share link and I'll extract the direct download URL for you.

<b>Supported domains:</b>
• terabox.com
• 1024tera.com
• teraboxapp.com
• 4funbox.co
• And many more...

<b>How to use:</b>
Just paste your Terabox link and I'll handle the rest!

⚠️ Note: Only use with content you have rights to download."""

    HELP = """📖 <b>Help Guide</b>

<b>Commands:</b>
/start - Show welcome message
/help - Show this help

<b>How to use:</b>
1. Copy a Terabox share link
2. Paste it in this chat
3. Wait for extraction
4. Get your direct download link!

<b>Tips:</b>
• Make sure the link is from a supported domain
• Some files may take longer to extract
• If extraction fails, try again in a few seconds"""

    PROCESSING = """⏳ <b>Processing your link...</b>

Please wait while I extract the download URL.
This may take up to 30 seconds."""

    INVALID_URL = """❌ <b>Invalid URL</b>

Please send a valid Terabox share link.

<b>Supported formats:</b>
• https://terabox.com/s/xxxxx
• https://1024tera.com/s/xxxxx
• etc."""

    ERROR = """❌ <b>Extraction Failed</b>

{error}

<b>Tips:</b>
• Make sure the link is valid and not expired
• The file must be publicly shared
• Try again in a few seconds"""

    @classmethod
    def success(
        cls,
        download_url: str,
        filename: Optional[str] = None,
        filesize: Optional[int] = None,
        filetype: Optional[str] = None
    ) -> str:
        """Format success message with file info"""
        parts = ["✅ <b>Download Link Extracted!</b>\n"]
        
        if filename:
            parts.append(f"📄 <b>File:</b> <code>{filename}</code>")
        
        if filesize:
            size_str = FileValidator.format_file_size(filesize)
            parts.append(f"📦 <b>Size:</b> {size_str}")
        
        if filetype:
            emoji = cls._get_type_emoji(filetype)
            parts.append(f"{emoji} <b>Type:</b> {filetype.capitalize()}")
        
        parts.append(f"\n🔗 <b>Download URL:</b>\n<code>{download_url}</code>")
        
        parts.append("\n\n💡 <i>Copy the link above to download your file!</i>")
        
        return "\n".join(parts)
    
    @staticmethod
    def _get_type_emoji(filetype: str) -> str:
        """Get emoji for file type"""
        emojis = {
            'video': '🎬',
            'audio': '🎵',
            'image': '🖼️',
            'document': '📄',
            'file': '📁'
        }
        return emojis.get(filetype.lower(), '📁')
