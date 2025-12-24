"""
Sandbox Service

Manages Docker containers for isolated code execution.

This module follows Clean Code principles:
- Single Responsibility: Separate classes for file ops, git ops, container ops
- Small Functions: Each method does one thing
- Named Constants: No magic numbers or strings
- Clear Error Handling: Consistent exception handling
"""

import logging
import os
import time
import threading
from typing import Dict, Any, List

import docker

from app.sandbox.constants import (
    CONTAINER_TIMEOUT_SECONDS,
    CONTAINER_MEMORY_LIMIT,
    CONTAINER_CPU_PERIOD,
    CONTAINER_CPU_QUOTA,
    CONTAINER_STOP_TIMEOUT,
    DEFAULT_WORKING_DIR,
    SANDBOX_DATA_DIR,
    HOME_DIR,
    LABEL_USER_ID,
    LABEL_TYPE,
    LABEL_CREATED_AT,
    SANDBOX_TYPE,
    DEFAULT_DEV_PORT,
    DEFAULT_GIT_EMAIL,
    DEFAULT_GIT_USER,
    NETRC_FILENAME,
    NETRC_PERMISSIONS,
    MAX_FILE_LIST_DEPTH,
    MAX_FILE_LIST_COUNT,
)
from app.sandbox.file_operations import FileOperations

logger = logging.getLogger(__name__)


class SandboxService:
    """
    Main service for managing sandbox containers.
    
    Responsibilities:
    - Container lifecycle management (create, destroy, list)
    - Command execution
    - Automatic cleanup scheduling
    """

    def __init__(self):
        self._client = None
        self._containers: Dict[str, Dict[str, Any]] = {}
        self._cleanup_timers: Dict[str, threading.Timer] = {}
        self._file_ops = FileOperations()

    @property
    def client(self):
        """Lazy-load the Docker client to avoid blocking during module import."""
        if self._client is None:
            self._client = docker.from_env()
        return self._client

    # ==================== Container Lifecycle ====================

    def create_sandbox(
        self,
        user_id: int,
        image: str = "node:18",
        timeout_seconds: int = CONTAINER_TIMEOUT_SECONDS,
    ) -> Dict[str, Any]:
        """Creates a new sandbox container with resource limits and auto-cleanup."""
        try:
            host_path = self._create_host_directory(user_id)
            container = self._start_container(user_id, image, host_path)
            
            self._register_container(container, user_id, host_path)
            self._schedule_cleanup(container.id, timeout_seconds)
            
            return self._build_create_response(container, image, host_path, timeout_seconds)
        except Exception as e:
            logger.error(f"Failed to create sandbox: {e}")
            raise

    def destroy_sandbox(self, container_id: str) -> Dict[str, Any]:
        """Stops and removes a container, freeing all resources."""
        self._cancel_cleanup_timer(container_id)
        
        try:
            container = self.client.containers.get(container_id)
            container.stop(timeout=CONTAINER_STOP_TIMEOUT)
            container.remove(force=True)
            self._unregister_container(container_id)
            
            return {
                "status": "destroyed",
                "container_id": container_id,
                "message": "Sandbox has been destroyed and resources freed",
            }
        except docker.errors.NotFound:
            self._unregister_container(container_id)
            return {"status": "already_destroyed", "container_id": container_id}
        except Exception as e:
            logger.error(f"Failed to destroy sandbox: {e}")
            return {"status": "error", "error": str(e)}

    def list_sandboxes(self, user_id: int) -> List[Dict[str, Any]]:
        """Lists all running sandboxes for a user."""
        containers = self.client.containers.list(
            filters={"label": [f"{LABEL_USER_ID}={user_id}", f"{LABEL_TYPE}={SANDBOX_TYPE}"]}
        )
        return [self._format_container_info(c) for c in containers]

    def cleanup_all_user_sandboxes(self, user_id: int) -> Dict[str, Any]:
        """Destroys all sandboxes for a user."""
        sandboxes = self.list_sandboxes(user_id)
        destroyed, errors = [], []
        
        for sandbox in sandboxes:
            result = self.destroy_sandbox(sandbox["container_id"])
            if result.get("status") in ["destroyed", "already_destroyed"]:
                destroyed.append(sandbox["container_id"])
            else:
                errors.append({
                    "container_id": sandbox["container_id"],
                    "error": result.get("error"),
                })
        
        return {"destroyed_count": len(destroyed), "destroyed": destroyed, "errors": errors}

    # ==================== Command Execution ====================

    def execute_command(
        self,
        container_id: str,
        command: str,
        workdir: str = DEFAULT_WORKING_DIR,
        background: bool = False,
        env: Dict[str, str] = None,
    ) -> Dict[str, Any]:
        """Executes a shell command inside the container."""
        try:
            container = self.client.containers.get(container_id)
            
            if background:
                return self._execute_background_command(container, command, workdir, env)
            return self._execute_foreground_command(container, command, workdir, env)
        except Exception as e:
            logger.error(f"Failed to execute command: {e}")
            raise

    # ==================== File Operations ====================

    def write_file(self, container_id: str, file_path: str, content: str) -> Dict[str, Any]:
        """Writes a file to the container."""
        try:
            container = self.client.containers.get(container_id)
            return self._file_ops.write_file(container, file_path, content)
        except Exception as e:
            logger.error(f"Failed to write file: {e}")
            raise

    def read_file(self, container_id: str, file_path: str) -> str:
        """Reads a file from the container."""
        try:
            container = self.client.containers.get(container_id)
            return self._file_ops.read_file(container, file_path)
        except Exception as e:
            logger.error(f"Failed to read file: {e}")
            raise

    def list_files(self, container_id: str, path: str = DEFAULT_WORKING_DIR) -> Dict[str, Any]:
        """Lists files in a directory within the container."""
        try:
            container = self.client.containers.get(container_id)
            absolute_path = self._ensure_absolute_path(path)
            
            result = container.exec_run(
                f"sh -c 'find {absolute_path} -maxdepth {MAX_FILE_LIST_DEPTH} "
                f"-type f -o -type d | head -{MAX_FILE_LIST_COUNT}'"
            )
            
            if result.exit_code != 0:
                return {"error": f"Failed to list files: {result.output.decode('utf-8')}"}
            
            files = self._parse_file_list(result.output)
            return {"path": absolute_path, "files": files, "count": len(files)}
        except Exception as e:
            logger.error(f"Failed to list files: {e}")
            raise

    # ==================== Git Operations ====================

    def setup_git_credentials(
        self,
        container_id: str,
        token: str,
        username: str = DEFAULT_GIT_USER,
    ) -> Dict[str, Any]:
        """Sets up Git credentials using .netrc for persistent authentication."""
        try:
            container = self.client.containers.get(container_id)
            
            self._write_netrc_file(container, username, token)
            self._configure_git(container)
            
            return {"status": "success", "message": "Git credentials configured"}
        except Exception as e:
            logger.error(f"Failed to setup git credentials: {e}")
            raise

    # ==================== Private Helper Methods ====================

    def _create_host_directory(self, user_id: int) -> str:
        """Creates a unique host directory for the sandbox."""
        timestamp = int(time.time())
        host_path = os.path.abspath(
            os.path.join(os.getcwd(), SANDBOX_DATA_DIR, str(user_id), str(timestamp))
        )
        os.makedirs(host_path, exist_ok=True)
        return host_path

    def _start_container(self, user_id: int, image: str, host_path: str):
        """Starts a new Docker container with resource limits."""
        container = self.client.containers.run(
            image,
            command="tail -f /dev/null",
            detach=True,
            ports={DEFAULT_DEV_PORT: None},
            working_dir=DEFAULT_WORKING_DIR,
            labels={
                LABEL_USER_ID: str(user_id),
                LABEL_TYPE: SANDBOX_TYPE,
                LABEL_CREATED_AT: str(int(time.time())),
            },
            volumes={host_path: {"bind": DEFAULT_WORKING_DIR, "mode": "rw"}},
            mem_limit=CONTAINER_MEMORY_LIMIT,
            cpu_period=CONTAINER_CPU_PERIOD,
            cpu_quota=CONTAINER_CPU_QUOTA,
            network_mode="bridge",
        )
        container.reload()
        return container

    def _register_container(self, container, user_id: int, host_path: str) -> None:
        """Registers a container in the internal tracking dict."""
        self._containers[container.id] = {
            "container": container,
            "user_id": user_id,
            "created_at": int(time.time()),
            "local_path": host_path,
        }

    def _unregister_container(self, container_id: str) -> None:
        """Removes a container from the internal tracking dict."""
        self._containers.pop(container_id, None)

    def _schedule_cleanup(self, container_id: str, timeout_seconds: int) -> None:
        """Schedules automatic container cleanup after timeout."""
        self._cancel_cleanup_timer(container_id)
        
        def cleanup():
            logger.info(f"Auto-cleanup triggered for container {container_id}")
            self.destroy_sandbox(container_id)
        
        timer = threading.Timer(timeout_seconds, cleanup)
        timer.daemon = True
        timer.start()
        self._cleanup_timers[container_id] = timer

    def _cancel_cleanup_timer(self, container_id: str) -> None:
        """Cancels the cleanup timer for a container."""
        timer = self._cleanup_timers.pop(container_id, None)
        if timer:
            timer.cancel()

    def _build_create_response(
        self, container, image: str, host_path: str, timeout_seconds: int
    ) -> Dict[str, Any]:
        """Builds the response dict for container creation."""
        return {
            "container_id": container.id,
            "status": "running",
            "host_port": self._get_exposed_port(container),
            "image": image,
            "local_path": host_path,
            "timeout_minutes": timeout_seconds // 60,
        }

    def _get_exposed_port(self, container) -> str | None:
        """Gets the exposed host port for the container."""
        ports = container.attrs["NetworkSettings"]["Ports"]
        if ports and DEFAULT_DEV_PORT in ports and ports[DEFAULT_DEV_PORT]:
            return ports[DEFAULT_DEV_PORT][0]["HostPort"]
        return None

    def _format_container_info(self, container) -> Dict[str, Any]:
        """Formats container info for listing."""
        return {
            "container_id": container.id,
            "image": container.image.tags[0] if container.image.tags else "unknown",
            "status": container.status,
            "host_port": self._get_exposed_port(container),
            "created_at": container.labels.get(LABEL_CREATED_AT, "unknown"),
        }

    def _execute_background_command(
        self, container, command: str, workdir: str, env: Dict[str, str] | None
    ) -> Dict[str, Any]:
        """Executes a command in background (detached)."""
        exec_id = container.client.api.exec_create(
            container.id,
            cmd=f"sh -c '{command}'",
            workdir=workdir,
            environment=env,
        )["Id"]
        container.client.api.exec_start(exec_id, detach=True)
        return {"output": "Command started in background", "exit_code": 0}

    def _execute_foreground_command(
        self, container, command: str, workdir: str, env: Dict[str, str] | None
    ) -> Dict[str, Any]:
        """Executes a command and waits for result."""
        result = container.exec_run(
            f"sh -c '{command}'",
            workdir=workdir,
            environment=env,
        )
        return {"output": result.output.decode("utf-8"), "exit_code": result.exit_code}

    def _write_netrc_file(self, container, username: str, token: str) -> None:
        """Writes .netrc file for GitHub authentication."""
        netrc_content = f"machine github.com\nlogin {username}\npassword {token}\n"
        self._file_ops.write_file_to_path(
            container, HOME_DIR, NETRC_FILENAME, netrc_content, NETRC_PERMISSIONS
        )
        container.exec_run(f"chmod 600 {HOME_DIR}/{NETRC_FILENAME}")

    def _configure_git(self, container) -> None:
        """Configures Git with default user info."""
        container.exec_run(f"git config --global user.email '{DEFAULT_GIT_EMAIL}'")
        container.exec_run(f"git config --global user.name '{DEFAULT_GIT_USER}'")
        container.exec_run("git config --global credential.helper store")

    @staticmethod
    def _ensure_absolute_path(path: str) -> str:
        """Ensures a path is absolute, prefixing with /app if needed."""
        if not path.startswith("/"):
            return f"{DEFAULT_WORKING_DIR}/{path}"
        return path

    @staticmethod
    def _parse_file_list(output: bytes) -> List[str]:
        """Parses the output of find command into a file list."""
        files = output.decode("utf-8").strip().split("\n")
        return [f for f in files if f]

    # ==================== Deprecated Methods ====================

    def stop_sandbox(self, container_id: str) -> Dict[str, Any]:
        """
        Deprecated: Use destroy_sandbox instead.
        """
        return self.destroy_sandbox(container_id)
