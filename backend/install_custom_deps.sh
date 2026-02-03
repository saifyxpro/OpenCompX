#!/bin/bash
set -e

# Define variables
REPO_URL="https://github.com/simular-ai/Agent-S.git"
CLONE_DIR="backend/temp_agent_s"

echo "Checking gui-agents installation..."

# Check if already installed
if pip show gui-agents > /dev/null 2>&1; then
    echo "gui-agents is already installed."
    # Optional: Check version or force reinstall if needed
    # For now, we assume if it's there, it's good (or the user will force reinstall manually)
    # To force update, user can run: pip uninstall -y gui-agents
else
    echo "gui-agents not found. Installing from source with patch..."
    
    # Clean up previous temp dir
    rm -rf "$CLONE_DIR"
    
    # Clone the repository
    echo "Cloning Agent-S repository..."
    git clone "$REPO_URL" "$CLONE_DIR"
    
    # Patch pyproject.toml to relax Python version constraint
    # Change requires-python = ">=3.9,<=3.12" to ">=3.9,<3.13" or similar
    # Using sed to replace the line. Adjust regex based on actual file content if needed.
    echo "Patching pyproject.toml..."
    if [ -f "$CLONE_DIR/pyproject.toml" ]; then
        # Replace <=3.12 with <3.13 to allow 3.12.11
        sed -i 's/<=3.12/<3.13/g' "$CLONE_DIR/pyproject.toml"
        echo "Patch applied."
    else
        echo "Error: pyproject.toml not found in cloned repo!"
        exit 1
    fi
    
    # Install the package
    echo "Installing patched gui-agents..."
    pip install "$CLONE_DIR"
    
    # Cleanup
    echo "Cleaning up..."
    rm -rf "$CLONE_DIR"
    
    echo "gui-agents installed successfully!"
fi
