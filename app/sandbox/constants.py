"""
Sandbox Constants

Centralized configuration for sandbox containers.
"""

# Container Timeouts
CONTAINER_TIMEOUT_SECONDS = 30 * 60  # 30 minutes default timeout
COMMAND_TIMEOUT_SECONDS = 60  # 60 seconds command timeout
CONTAINER_STOP_TIMEOUT = 5  # Seconds to wait before force stop

# Resource Limits
CONTAINER_MEMORY_LIMIT = "512m"  # 512MB memory limit
CONTAINER_CPU_PERIOD = 100000  # CPU period in microseconds
CONTAINER_CPU_QUOTA = 50000  # 50% of one CPU core

# Paths
DEFAULT_WORKING_DIR = "/app"
SANDBOX_DATA_DIR = "sandbox_data"
HOME_DIR = "/root"

# Container Labels
LABEL_USER_ID = "user_id"
LABEL_TYPE = "type"
LABEL_CREATED_AT = "created_at"
SANDBOX_TYPE = "sandbox"

# Ports
DEFAULT_DEV_PORT = "3000/tcp"

# Git Configuration
DEFAULT_GIT_EMAIL = "agent@example.com"
DEFAULT_GIT_USER = "AI Agent"
NETRC_FILENAME = ".netrc"
NETRC_PERMISSIONS = 0o600

# File Listing
MAX_FILE_LIST_DEPTH = 2
MAX_FILE_LIST_COUNT = 100

