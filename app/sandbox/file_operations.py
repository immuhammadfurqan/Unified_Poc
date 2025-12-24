"""
File Operations

Handles all file read/write operations for Docker containers.
Extracted to follow Single Responsibility Principle.
"""

import io
import os
import tarfile
from typing import Dict, Any

from app.sandbox.constants import DEFAULT_WORKING_DIR


class FileOperations:
    """
    Handles file operations within Docker containers.
    
    Uses tar archives for file transfer as required by Docker API.
    """

    def write_file(self, container, file_path: str, content: str) -> Dict[str, Any]:
        """
        Writes a file to the container at the specified path.
        
        Args:
            container: Docker container object
            file_path: Path within container (relative to /app or absolute)
            content: File content as string
            
        Returns:
            Dict with status and path
        """
        tar_stream = self._create_tar_stream(file_path, content)
        dir_path = self._resolve_directory_path(file_path)
        
        container.exec_run(f"mkdir -p {dir_path}")
        container.put_archive(path=dir_path, data=tar_stream)
        
        return {"status": "success", "path": file_path}

    def write_file_to_path(
        self, 
        container, 
        directory: str, 
        filename: str, 
        content: str, 
        mode: int = None
    ) -> None:
        """
        Writes a file to a specific directory with optional permissions.
        
        Args:
            container: Docker container object
            directory: Target directory path
            filename: Name of the file
            content: File content as string
            mode: Optional file permissions (e.g., 0o600)
        """
        tar_stream = self._create_tar_stream(filename, content, mode)
        container.put_archive(path=directory, data=tar_stream)

    def read_file(self, container, file_path: str) -> str:
        """
        Reads a file from the container.
        
        Args:
            container: Docker container object
            file_path: Path within container (relative to /app or absolute)
            
        Returns:
            File content as string
        """
        absolute_path = self._ensure_absolute_path(file_path)
        bits, _ = container.get_archive(absolute_path)
        
        return self._extract_file_content(bits)

    def _create_tar_stream(self, file_path: str, content: str, mode: int = None) -> io.BytesIO:
        """Creates a tar stream for writing to Docker container."""
        tar_stream = io.BytesIO()
        
        with tarfile.open(fileobj=tar_stream, mode="w") as tar:
            file_data = content.encode("utf-8")
            info = tarfile.TarInfo(name=os.path.basename(file_path))
            info.size = len(file_data)
            
            if mode is not None:
                info.mode = mode
                
            tar.addfile(info, io.BytesIO(file_data))
        
        tar_stream.seek(0)
        return tar_stream

    def _extract_file_content(self, archive_bits) -> str:
        """Extracts file content from a tar archive stream."""
        file_content = io.BytesIO()
        
        for chunk in archive_bits:
            file_content.write(chunk)
        file_content.seek(0)
        
        with tarfile.open(fileobj=file_content, mode="r") as tar:
            member = tar.next()
            if member and member.isfile():
                extracted = tar.extractfile(member)
                if extracted:
                    return extracted.read().decode("utf-8")
        
        return ""

    @staticmethod
    def _resolve_directory_path(file_path: str) -> str:
        """Resolves the directory path for a file."""
        dir_path = os.path.dirname(file_path)
        
        if not dir_path:
            return DEFAULT_WORKING_DIR
        if not dir_path.startswith("/"):
            return f"{DEFAULT_WORKING_DIR}/{dir_path}"
        
        return dir_path

    @staticmethod
    def _ensure_absolute_path(file_path: str) -> str:
        """Ensures a path is absolute, prefixing with /app if needed."""
        if not file_path.startswith("/"):
            return f"{DEFAULT_WORKING_DIR}/{file_path}"
        return file_path

