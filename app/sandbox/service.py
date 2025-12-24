import docker
import logging
from typing import Dict, Any, Optional, List
import tarfile
import io
import os

logger = logging.getLogger(__name__)

class SandboxService:
    def __init__(self):
        self._client = None
        self.containers: Dict[str, Any] = {}
    
    @property
    def client(self):
        """Lazy-load the Docker client to avoid blocking during module import."""
        if self._client is None:
            self._client = docker.from_env()
        return self._client

    def create_sandbox(self, user_id: int, image: str = "node:18") -> Dict[str, Any]:
        """
        Creates a new sandbox container for the user.
        """
        try:
            # Determine command based on image
            command = "tail -f /dev/null"  # Keep container running
            
            # Create local mount directory for code visibility
            import time
            timestamp = int(time.time())
            # Use absolute path for Windows/Linux compatibility
            host_path = os.path.abspath(os.path.join(os.getcwd(), "sandbox_data", str(user_id), str(timestamp)))
            os.makedirs(host_path, exist_ok=True)
            
            container = self.client.containers.run(
                image,
                command=command,
                detach=True,
                # publish_all_ports=True, # We might need this later
                ports={'3000/tcp': None}, # Expose common dev port
                working_dir="/app",
                labels={"user_id": str(user_id), "type": "sandbox"},
                volumes={host_path: {'bind': '/app', 'mode': 'rw'}}
            )
            
            # Reload to get network settings (ports)
            container.reload()
            
            # Store reference
            self.containers[container.id] = container
            
            # Get exposed port
            ports = container.attrs['NetworkSettings']['Ports']
            host_port = None
            if ports and '3000/tcp' in ports and ports['3000/tcp']:
                host_port = ports['3000/tcp'][0]['HostPort']
            
            return {
                "container_id": container.id,
                "status": "running",
                "host_port": host_port,
                "image": image,
                "local_path": host_path
            }
        except Exception as e:
            logger.error(f"Failed to create sandbox: {e}")
            raise e

    def execute_command(self, container_id: str, command: str, workdir: str = "/app", background: bool = False) -> Dict[str, Any]:
        """
        Executes a shell command inside the container.
        """
        try:
            container = self.client.containers.get(container_id)
            
            if background:
                # Run detached
                exec_id = container.client.api.exec_create(
                    container.id, 
                    cmd=f"sh -c '{command}'",
                    workdir=workdir
                )['Id']
                container.client.api.exec_start(exec_id, detach=True)
                return {"output": "Command started in background", "exit_code": 0}
            
            # Run and wait
            result = container.exec_run(
                f"sh -c '{command}'",
                workdir=workdir
            )
            
            return {
                "output": result.output.decode('utf-8'),
                "exit_code": result.exit_code
            }
        except Exception as e:
            logger.error(f"Failed to execute command: {e}")
            raise e

    def write_file(self, container_id: str, file_path: str, content: str) -> Dict[str, Any]:
        """
        Writes a file to the container.
        """
        try:
            container = self.client.containers.get(container_id)
            
            # Docker put_archive expects a tar stream
            tar_stream = io.BytesIO()
            with tarfile.open(fileobj=tar_stream, mode='w') as tar:
                # Create file info
                file_data = content.encode('utf-8')
                info = tarfile.TarInfo(name=os.path.basename(file_path))
                info.size = len(file_data)
                tar.addfile(info, io.BytesIO(file_data))
            
            tar_stream.seek(0)
            
            # Determine directory path
            dir_path = os.path.dirname(file_path)
            if not dir_path:
                dir_path = "/app"
            elif not dir_path.startswith("/"):
                dir_path = f"/app/{dir_path}"
                
            # Ensure directory exists
            container.exec_run(f"mkdir -p {dir_path}")
            
            container.put_archive(
                path=dir_path,
                data=tar_stream
            )
            
            return {"status": "success", "path": file_path}
        except Exception as e:
            logger.error(f"Failed to write file: {e}")
            raise e

    def read_file(self, container_id: str, file_path: str) -> str:
        """
        Reads a file from the container.
        """
        try:
            container = self.client.containers.get(container_id)
            
            bits, stat = container.get_archive(file_path)
            
            file_content = io.BytesIO()
            for chunk in bits:
                file_content.write(chunk)
            file_content.seek(0)
            
            with tarfile.open(fileobj=file_content, mode='r') as tar:
                member = tar.next()
                if member:
                    return tar.extractfile(member).read().decode('utf-8')
            return ""
        except Exception as e:
            logger.error(f"Failed to read file: {e}")
            raise e

    def stop_sandbox(self, container_id: str) -> Dict[str, Any]:
        """
        Stops and removes the container.
        """
        try:
            container = self.client.containers.get(container_id)
            container.stop()
            container.remove()
            if container_id in self.containers:
                del self.containers[container_id]
            return {"status": "stopped", "container_id": container_id}
        except Exception as e:
            logger.error(f"Failed to stop sandbox: {e}")
            # Don't raise if it's already gone
            return {"status": "error", "error": str(e)}

    def list_sandboxes(self, user_id: int) -> List[Dict[str, Any]]:
        """
        Lists running sandboxes for a user.
        """
        # Get containers with matching label
        containers = self.client.containers.list(
            filters={"label": [f"user_id={user_id}", "type=sandbox"]}
        )
        
        results = []
        for c in containers:
            ports = c.attrs['NetworkSettings']['Ports']
            host_port = None
            if ports and '3000/tcp' in ports and ports['3000/tcp']:
                host_port = ports['3000/tcp'][0]['HostPort']
                
            results.append({
                "container_id": c.id,
                "image": c.image.tags[0] if c.image.tags else "unknown",
                "status": c.status,
                "host_port": host_port
            })
        return results

