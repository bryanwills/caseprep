"""
File processing service for handling media files and metadata extraction.
"""

import mimetypes
import subprocess
import json
from typing import Optional, Dict, Any
from pathlib import Path


class FileProcessingService:
    """Service for processing and analyzing uploaded files."""
    
    def __init__(self):
        self.supported_audio_types = {
            "audio/mpeg", "audio/mp3", "audio/wav", "audio/aac", 
            "audio/ogg", "audio/flac", "audio/m4a", "audio/webm"
        }
        
        self.supported_video_types = {
            "video/mp4", "video/avi", "video/mov", "video/wmv", 
            "video/flv", "video/webm", "video/mkv"
        }
        
        self.supported_document_types = {
            "application/pdf", "text/plain", "application/msword",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        }
        
        self.supported_image_types = {
            "image/jpeg", "image/jpg", "image/png", "image/gif", 
            "image/bmp", "image/tiff", "image/webp"
        }
    
    def get_mime_type(self, filename: str) -> Optional[str]:
        """Get MIME type from filename."""
        mime_type, _ = mimetypes.guess_type(filename)
        return mime_type
    
    def is_supported_file_type(self, mime_type: str) -> bool:
        """Check if file type is supported."""
        return mime_type in (
            self.supported_audio_types | 
            self.supported_video_types | 
            self.supported_document_types | 
            self.supported_image_types
        )
    
    def get_file_category(self, mime_type: str) -> Optional[str]:
        """Get file category from MIME type."""
        if mime_type in self.supported_audio_types:
            return "audio"
        elif mime_type in self.supported_video_types:
            return "video"
        elif mime_type in self.supported_document_types:
            return "document"
        elif mime_type in self.supported_image_types:
            return "image"
        return None
    
    def validate_file_size(self, file_size: int, max_size_mb: int = 500) -> bool:
        """Validate file size against limits."""
        max_size_bytes = max_size_mb * 1024 * 1024
        return file_size <= max_size_bytes
    
    async def extract_media_metadata(self, file_path: str) -> Dict[str, Any]:
        """Extract metadata from media files using ffprobe."""
        try:
            # Use ffprobe to extract metadata
            cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                file_path
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                return {}
            
            metadata = json.loads(result.stdout)
            
            # Extract useful information
            extracted = {
                "duration_seconds": 0,
                "bitrate": None,
                "sample_rate": None,
                "channels": None,
                "width": None,
                "height": None,
                "frame_rate": None,
                "codec": None,
                "format_name": None
            }
            
            # Get format information
            if "format" in metadata:
                format_info = metadata["format"]
                extracted["duration_seconds"] = float(format_info.get("duration", 0))
                extracted["bitrate"] = int(format_info.get("bit_rate", 0)) if format_info.get("bit_rate") else None
                extracted["format_name"] = format_info.get("format_name")
            
            # Get stream information
            if "streams" in metadata:
                for stream in metadata["streams"]:
                    codec_type = stream.get("codec_type")
                    
                    if codec_type == "audio":
                        extracted["sample_rate"] = int(stream.get("sample_rate", 0)) if stream.get("sample_rate") else None
                        extracted["channels"] = int(stream.get("channels", 0)) if stream.get("channels") else None
                        if not extracted["codec"]:
                            extracted["codec"] = stream.get("codec_name")
                    
                    elif codec_type == "video":
                        extracted["width"] = int(stream.get("width", 0)) if stream.get("width") else None
                        extracted["height"] = int(stream.get("height", 0)) if stream.get("height") else None
                        
                        # Parse frame rate
                        r_frame_rate = stream.get("r_frame_rate")
                        if r_frame_rate:
                            try:
                                num, den = map(int, r_frame_rate.split("/"))
                                if den != 0:
                                    extracted["frame_rate"] = round(num / den, 2)
                            except (ValueError, ZeroDivisionError):
                                pass
                        
                        if not extracted["codec"]:
                            extracted["codec"] = stream.get("codec_name")
            
            return extracted
            
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, json.JSONDecodeError):
            return {}
    
    async def generate_audio_waveform(self, file_path: str, output_path: str) -> bool:
        """Generate waveform image for audio file."""
        try:
            cmd = [
                'ffmpeg',
                '-i', file_path,
                '-filter_complex', 'showwavespic=s=1200x200:colors=0x3b82f6',
                '-frames:v', '1',
                '-y',  # Overwrite output file
                output_path
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            return result.returncode == 0
            
        except subprocess.TimeoutExpired:
            return False
    
    async def generate_video_thumbnail(self, file_path: str, output_path: str, timestamp: str = "00:00:01") -> bool:
        """Generate thumbnail for video file."""
        try:
            cmd = [
                'ffmpeg',
                '-i', file_path,
                '-ss', timestamp,
                '-vframes', '1',
                '-q:v', '2',
                '-y',  # Overwrite output file
                output_path
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            return result.returncode == 0
            
        except subprocess.TimeoutExpired:
            return False
    
    async def convert_to_wav(self, input_path: str, output_path: str) -> bool:
        """Convert audio file to WAV format for transcription."""
        try:
            cmd = [
                'ffmpeg',
                '-i', input_path,
                '-acodec', 'pcm_s16le',
                '-ac', '1',  # Mono
                '-ar', '16000',  # 16kHz sample rate for Whisper
                '-y',  # Overwrite output file
                output_path
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes for large files
            )
            
            return result.returncode == 0
            
        except subprocess.TimeoutExpired:
            return False
    
    def get_file_extension(self, filename: str) -> str:
        """Get file extension from filename."""
        return Path(filename).suffix.lower()
    
    def sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for safe storage."""
        # Remove or replace unsafe characters
        unsafe_chars = '<>:"/\\|?*'
        sanitized = filename
        
        for char in unsafe_chars:
            sanitized = sanitized.replace(char, '_')
        
        # Limit length
        name, ext = Path(sanitized).stem, Path(sanitized).suffix
        if len(name) > 200:
            name = name[:200]
        
        return f"{name}{ext}"
    
    async def analyze_document_content(self, file_path: str, mime_type: str) -> Dict[str, Any]:
        """Analyze document content and extract text if possible."""
        analysis = {
            "page_count": 0,
            "text_preview": "",
            "has_text": False,
            "language": None
        }
        
        try:
            if mime_type == "application/pdf":
                # For PDF files, you might use PyPDF2 or similar
                # This is a placeholder for actual implementation
                pass
            elif mime_type == "text/plain":
                # Read text file
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read(1000)  # First 1000 characters
                    analysis["text_preview"] = content
                    analysis["has_text"] = bool(content.strip())
        
        except Exception:
            pass
        
        return analysis