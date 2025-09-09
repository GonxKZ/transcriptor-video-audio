"""
Application configuration and settings management.
"""
import os
import json
from typing import Optional, Dict, Any
from dataclasses import dataclass, asdict
from pathlib import Path

@dataclass
class AppSettings:
    """Application settings data class."""
    
    # Audio processing settings
    normalize_loudness: bool = True
    apply_noise_suppression: bool = False
    
    # Transcription settings
    model_size: str = "large-v3"  # tiny, base, small, medium, large-v3
    language: Optional[str] = None  # None for auto-detection
    beam_size: int = 5
    temperature: float = 0.0
    use_word_alignment: bool = True
    use_diarization: bool = False
    
    # Diarization settings
    hf_token: Optional[str] = None
    
    # Backend settings
    backend: str = "cuda"  # cuda, cpu, directml
    
    # UI settings
    theme: str = "auto"  # auto, light, dark
    show_guided_tours: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert settings to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AppSettings":
        """Create settings from dictionary."""
        return cls(**data)

class ConfigManager:
    """Manages application configuration."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize configuration manager."""
        if config_path is None:
            # Use user's home directory for config
            config_dir = Path.home() / ".transcriptor"
            config_dir.mkdir(exist_ok=True)
            self.config_path = config_dir / "settings.json"
        else:
            self.config_path = Path(config_path)
            
        self.settings = AppSettings()
        self.load_settings()
    
    def load_settings(self) -> bool:
        """Load settings from file."""
        if not self.config_path.exists():
            self.save_settings()  # Create default config
            return False
            
        try:
            with open(self.config_path, 'r') as f:
                data = json.load(f)
                self.settings = AppSettings.from_dict(data)
            return True
        except Exception as e:
            print(f"Error loading settings: {e}")
            return False
    
    def save_settings(self) -> bool:
        """Save settings to file."""
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self.settings.to_dict(), f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving settings: {e}")
            return False
    
    def update_settings(self, **kwargs) -> bool:
        """Update settings with provided values."""
        for key, value in kwargs.items():
            if hasattr(self.settings, key):
                setattr(self.settings, key, value)
        return self.save_settings()