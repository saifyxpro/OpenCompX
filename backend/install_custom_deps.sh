#!/bin/bash
set -e

# Define variables
REPO_URL="https://github.com/simular-ai/Agent-S.git"
CLONE_DIR="backend/temp_agent_s"

echo "Checking gui-agents installation..."

echo "Forcing gui-agents installation from source..."

# Always uninstall existing version to ensure we get the patched one
pip uninstall -y gui-agents || true

# Clean up previous temp dir
rm -rf "$CLONE_DIR"

# Clone the repository
echo "Cloning Agent-S repository..."
git clone "$REPO_URL" "$CLONE_DIR"

# Patch setup.py to relax Python version constraint (since pyproject.toml might not exist or control build)
echo "Patching setup.py..."
if [ -f "$CLONE_DIR/setup.py" ]; then
    # Replace python_requires='>=3.9,<=3.12' with python_requires='>=3.9,<3.13'
    # Using sed to be flexible with quotes and spacing
    sed -i "s/python_requires=['\"]>=3.9,<=3.12['\"]/python_requires='>=3.9,<3.13'/g" "$CLONE_DIR/setup.py"
    # Fallback: if it uses double quotes or different spacing, try a broader regex if the above fails
    # Or just blindly replace <=3.12 with <3.13 globally in the file (risky but effective for quick fix)
    sed -i 's/<=3.12/<3.13/g' "$CLONE_DIR/setup.py"
    echo "Patch applied to setup.py."
elif [ -f "$CLONE_DIR/pyproject.toml" ]; then
    # Keep pyproject.toml fallback just in case
    sed -i 's/<=3.12/<3.13/g' "$CLONE_DIR/pyproject.toml"
    echo "Patch applied to pyproject.toml."
else
    echo "Error: Neither setup.py nor pyproject.toml found!"
    ls -R "$CLONE_DIR"
    exit 1
fi

# Install the package
echo "Installing patched gui-agents..."
pip install "$CLONE_DIR"

# Cleanup
echo "Cleaning up..."
rm -rf "$CLONE_DIR"

echo "gui-agents installed successfully!"
