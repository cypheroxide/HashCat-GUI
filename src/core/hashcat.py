"""
Hashcat process management and command building module.
Handles hashcat execution, monitoring, and result parsing.
"""
import os
import subprocess
import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Union
from dataclasses import dataclass
from datetime import datetime

@dataclass
class HashcatStatus:
    """Status information for a hashcat process"""
    status: str
    progress: float
    speed: str
    estimated_completion: str
    recovered_hashes: int
    total_hashes: int
    time_started: datetime

class HashcatError(Exception):
    """Base exception for hashcat-related errors"""
    pass

class CommandError(HashcatError):
    """Invalid command or arguments"""
    pass

class ExecutionError(HashcatError):
    """Process execution failed"""
    pass

class HashcatRunner:
    """Manages hashcat process execution and monitoring"""
    
    def __init__(self, config):
        self.config = config
        self.process: Optional[subprocess.Popen] = None
        self.command: List[str] = []
        self._validate_hashcat_binary()
    
    def _validate_hashcat_binary(self) -> None:
        """Verify hashcat binary exists and is executable"""
        hashcat_path = self.config.get_path('hashcat')
        if not hashcat_path.exists():
            raise HashcatError(f"Hashcat binary not found at {hashcat_path}")
        if not os.access(hashcat_path, os.X_OK):
            raise HashcatError(f"Hashcat binary at {hashcat_path} is not executable")
    
    def build_command(self, 
                    hash_type: int,
                    hash_file: Union[str, Path],
                    attack_mode: int = 0,
                    wordlist: Optional[Union[str, Path]] = None,
                    rule: Optional[Union[str, Path]] = None,
                    mask: Optional[str] = None) -> List[str]:
        """Build hashcat command with given parameters"""
        cmd = [
            str(self.config.get_path('hashcat')),
            '--status',
            '--status-timer=1',
            '--machine-readable',
            '--quiet',
            '--potfile-path', str(self.config.get_path('potfile')),
            '-m', str(hash_type),
            '-a', str(attack_mode),
            str(hash_file)
        ]
        
        # Add attack-specific parameters
        if attack_mode == 0:  # Wordlist attack
            if not wordlist:
                raise CommandError("Wordlist required for attack mode 0")
            cmd.append(str(wordlist))
            if rule:
                cmd.extend(['-r', str(rule)])
        elif attack_mode == 3:  # Brute force attack
            if not mask:
                raise CommandError("Mask required for attack mode 3")
            cmd.append(str(mask))
        
        self.command = cmd
        return cmd
    
    def start(self) -> None:
        """Start hashcat process"""
        if not self.command:
            raise CommandError("Command not built. Call build_command first.")
        
        try:
            self.process = subprocess.Popen(
                self.command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )
        except subprocess.SubprocessError as e:
            raise ExecutionError(f"Failed to start hashcat: {e}")
    
    def stop(self) -> None:
        """Stop hashcat process"""
        if self.process and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
    
    def get_status(self) -> HashcatStatus:
        """Get current status of hashcat process"""
        if not self.process:
            raise HashcatError("No active process")
        
        if self.process.poll() is not None:
            return HashcatStatus(
                status="Finished" if self.process.returncode == 0 else "Failed",
                progress=100 if self.process.returncode == 0 else 0,
                speed="0 H/s",
                estimated_completion="",
                recovered_hashes=0,
                total_hashes=0,
                time_started=datetime.now()
            )
        
        # Read latest status from process output
        status_line = ""
        while True:
            line = self.process.stdout.readline()
            if not line:
                break
            if line.startswith("STATUS"):
                status_line = line
        
        return self._parse_status(status_line)
    
    def _parse_status(self, status_line: str) -> HashcatStatus:
        """Parse hashcat status output"""
        if not status_line:
            return HashcatStatus(
                status="Running",
                progress=0,
                speed="0 H/s",
                estimated_completion="",
                recovered_hashes=0,
                total_hashes=0,
                time_started=datetime.now()
            )
        
        try:
            parts = status_line.split('\t')
            return HashcatStatus(
                status=parts[1],
                progress=float(parts[2]),
                speed=f"{parts[3]} H/s",
                estimated_completion=parts[4],
                recovered_hashes=int(parts[5]),
                total_hashes=int(parts[6]),
                time_started=datetime.fromtimestamp(float(parts[7]))
            )
        except (IndexError, ValueError) as e:
            raise HashcatError(f"Failed to parse status: {e}")
    
    def get_results(self) -> Dict[str, str]:
        """Get cracking results"""
        if not self.process:
            return {}
        
        potfile = self.config.get_path('potfile')
        if not potfile.exists():
            return {}
        
        results = {}
        with open(potfile, 'r') as f:
            for line in f:
                try:
                    hash_val, password = line.strip().split(':')
                    results[hash_val] = password
                except ValueError:
                    continue
        
        return results

