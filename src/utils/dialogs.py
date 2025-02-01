"""File and directory selection dialog utilities using PyQt5.

This module provides a clean interface for showing file and directory selection
dialogs using PyQt5. It handles the Qt application lifecycle and provides both
synchronous and asynchronous dialog options.
"""
from typing import List, Optional, Union
from pathlib import Path
import sys
from functools import wraps

from PyQt5.QtWidgets import QApplication, QFileDialog
from PyQt5.QtCore import Qt

class DialogError(Exception):
    """Base exception class for dialog-related errors."""
    pass

def ensure_qapp(f):
    """Decorator to ensure a QApplication instance exists before running the function."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not QApplication.instance():
            QApplication(sys.argv)
        return f(*args, **kwargs)
    return wrapper

@ensure_qapp
def get_open_file(
    caption: str = "Open File",
    directory: Union[str, Path] = ".",
    filter: str = "All Files (*.*)",
    multiple: bool = False
) -> Union[Optional[Path], List[Path]]:
    """Show a file selection dialog for opening files.
    
    Args:
        caption: Dialog window title
        directory: Initial directory to show
        filter: File type filter (e.g. "Images (*.png *.jpg)")
        multiple: Allow multiple file selection
    
    Returns:
        Path object(s) for selected file(s) or None if cancelled
        Returns a list of Paths if multiple=True
    
    Raises:
        DialogError: If there's an error showing the dialog
    """
    try:
        if multiple:
            files, _ = QFileDialog.getOpenFileNames(
                None, caption, str(directory), filter
            )
            return [Path(f) for f in files] if files else None
        else:
            file, _ = QFileDialog.getOpenFileName(
                None, caption, str(directory), filter
            )
            return Path(file) if file else None
    except Exception as e:
        raise DialogError(f"Error showing file open dialog: {e}")

@ensure_qapp
def get_save_file(
    caption: str = "Save File",
    directory: Union[str, Path] = ".",
    filter: str = "All Files (*.*)"
) -> Optional[Path]:
    """Show a file selection dialog for saving a file.
    
    Args:
        caption: Dialog window title
        directory: Initial directory to show
        filter: File type filter
    
    Returns:
        Path object for selected file or None if cancelled
    
    Raises:
        DialogError: If there's an error showing the dialog
    """
    try:
        file, _ = QFileDialog.getSaveFileName(
            None, caption, str(directory), filter
        )
        return Path(file) if file else None
    except Exception as e:
        raise DialogError(f"Error showing file save dialog: {e}")

@ensure_qapp
def get_directory(
    caption: str = "Select Directory",
    directory: Union[str, Path] = "."
) -> Optional[Path]:
    """Show a directory selection dialog.
    
    Args:
        caption: Dialog window title
        directory: Initial directory to show
    
    Returns:
        Path object for selected directory or None if cancelled
    
    Raises:
        DialogError: If there's an error showing the dialog
    """
    try:
        dir = QFileDialog.getExistingDirectory(
            None, caption, str(directory),
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
        )
        return Path(dir) if dir else None
    except Exception as e:
        raise DialogError(f"Error showing directory selection dialog: {e}")

async def async_get_open_file(*args, **kwargs) -> Union[Optional[Path], List[Path]]:
    """Async version of get_open_file."""
    return get_open_file(*args, **kwargs)

async def async_get_save_file(*args, **kwargs) -> Optional[Path]:
    """Async version of get_save_file."""
    return get_save_file(*args, **kwargs)

async def async_get_directory(*args, **kwargs) -> Optional[Path]:
    """Async version of get_directory."""
    return get_directory(*args, **kwargs)

