"""
Configuration management module for Linux-based systems.
Handles distribution detection, path resolution, and config validation.
"""
from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path
import os
import yaml
from typing import Dict, Optional, TypedDict
import shutil
from pydantic import BaseModel, validator

class LinuxDistribution(Enum):
    """Supported Linux distributions"""
    DEBIAN = auto()  # Debian/Kali
    ARCH = auto()    # Arch/BlackArch
    UNKNOWN = auto()

class PathConfig(TypedDict):
    """Type definitions for path configuration"""
    hashcat: str
    wordlists: str
    rules: str
    temp: str
    potfile: str

@dataclass
class SystemPaths:
    """System path configurations for different distributions"""
    DEBIAN: PathConfig = {
        'hashcat': '/usr/bin/hashcat',
        'wordlists': '/usr/share/wordlists',
        'rules': '/usr/share/hashcat/rules',
        'temp': '/tmp',
        'potfile': '~/.hashcat/hashcat.potfile'
    }
    
    ARCH: PathConfig = {
        'hashcat': '/usr/bin/hashcat',
        'wordlists': '/usr/share/wordlists',
        'rules': '/usr/share/hashcat/rules',
        'temp': '/tmp',
        'potfile': '~/.hashcat/hashcat.potfile'
    }

class ConfigModel(BaseModel):
    """Configuration validation model"""
    paths: Dict[str, str]
    debug: bool = False
    log_level: str = "INFO"
    max_processes: int = 4
    theme: str = "dark"
    language: str = "en"
    show_notifications: bool = True
    auto_update_check: bool = True
    
    @validator('paths')
    def validate_paths(cls, v):
        required = {'hashcat', 'wordlists', 'rules', 'temp', 'potfile'}
        if missing := required - set(v.keys()):
            raise ValueError(f"Missing required paths: {missing}")
        return v
    
    @validator('log_level')
    def validate_log_level(cls, v):
        valid_levels = {'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'}
        if v.upper() not in valid_levels:
            raise ValueError(f"Invalid log level. Must be one of {valid_levels}")
        return v.upper()
        
    @validator('theme')
    def validate_theme(cls, v):
        valid_themes = {'light', 'dark', 'system'}
        if v.lower() not in valid_themes:
            raise ValueError(f"Invalid theme. Must be one of {valid_themes}")
        return v.lower()
        
    @validator('language')
    def validate_language(cls, v):
        valid_languages = {'en', 'es', 'fr', 'de'}
        if v.lower() not in valid_languages:
            raise ValueError(f"Invalid language. Must be one of {valid_languages}")
        return v.lower()

class Config:
    """Main configuration class"""
    def __init__(self):
        self.distribution = self._detect_distribution()
        self.config_dir = self._get_config_dir()
        self.config_file = self.config_dir / 'config.yml'
        self.data_dir = self._get_data_dir()
        self.config = self._load_config()
        self._setup_directories()
    
    @staticmethod
    def _detect_distribution() -> LinuxDistribution:
        """Detect the current Linux distribution"""
        if os.path.exists('/etc/debian_version'):
            return LinuxDistribution.DEBIAN
        elif os.path.exists('/etc/arch-release'):
            return LinuxDistribution.ARCH
        return LinuxDistribution.UNKNOWN
    
    @staticmethod
    def _get_config_dir() -> Path:
        """Get the configuration directory using XDG standard"""
        xdg_config = os.environ.get('XDG_CONFIG_HOME', os.path.expanduser('~/.config'))
        config_dir = Path(xdg_config) / 'hashbreaker'
        config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir
    
    def _load_config(self) -> ConfigModel:
        """Load or create configuration file"""
        if not self.config_file.exists():
            return self._create_default_config()
        
        with open(self.config_file, 'r') as f:
            config_data = yaml.safe_load(f)
        
        return ConfigModel(**config_data)
    
    def _create_default_config(self) -> ConfigModel:
        """Create default configuration based on detected distribution"""
        paths = getattr(SystemPaths, self.distribution.name, SystemPaths.DEBIAN)
        config_data = {
            'paths': paths,
            'debug': False,
            'log_level': 'INFO',
            'max_processes': 4
        }
        
        config = ConfigModel(**config_data)
        self.save_config(config)
        return config
    
    def save_config(self, config: ConfigModel) -> None:
        """Save configuration to file"""
        with open(self.config_file, 'w') as f:
            yaml.safe_dump(config.dict(), f)
    
    def get_path(self, path_type: str) -> Path:
        """Resolve and return a specific path"""
        if path_type not in self.config.paths:
            raise KeyError(f"Unknown path type: {path_type}")
        
        path = Path(os.path.expanduser(self.config.paths[path_type]))
        return path
    
    def verify_paths(self) -> Dict[str, bool]:
        """Verify that all configured paths exist and are accessible"""
        results = {}
        for path_type, path_str in self.config.paths.items():
            path = Path(os.path.expanduser(path_str))
            results[path_type] = path.exists()
        return results
    
    def verify_binaries(self) -> Dict[str, bool]:
        """Verify that required binaries are available"""
        binaries = ['hashcat']
        results = {}
        for binary in binaries:
            results[binary] = shutil.which(binary) is not None
        return results

        def _get_data_dir(self) -> Path:
            """Get the data directory for storing application data"""
            xdg_data = os.environ.get('XDG_DATA_HOME', os.path.expanduser('~/.local/share'))
            data_dir = Path(xdg_data) / 'hashcat-gui'
            data_dir.mkdir(parents=True, exist_ok=True)
            return data_dir

        def _setup_directories(self) -> None:
            """Setup required application directories"""
            directories = {
                'wordlists': self.data_dir / 'wordlists',
                'rules': self.data_dir / 'rules',
                'masks': self.data_dir / 'masks',
                'sessions': self.data_dir / 'sessions',
                'logs': self.data_dir / 'logs'
            }
            
            for dir_path in directories.values():
                dir_path.mkdir(parents=True, exist_ok=True)

        def get_env_override(self, key: str) -> Optional[str]:
            """Get environment variable override for config value"""
            env_key = f"HASHCATGUI_{key.upper()}"
            return os.environ.get(env_key)

        def migrate_old_config(self) -> None:
            """Migrate configuration from older versions"""
            if not self.config_file.exists():
                return
                
            with open(self.config_file, 'r') as f:
                old_config = yaml.safe_load(f)
                
            version = old_config.get('version', '0.0.0')
            if version < '0.1.0':
                # Perform migration steps here
                old_config['version'] = '0.1.0'
                
            with open(self.config_file, 'w') as f:
                yaml.safe_dump(old_config, f)
