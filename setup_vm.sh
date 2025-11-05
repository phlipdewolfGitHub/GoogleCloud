#!/bin/bash
#
# Setup script for Google Cloud VM to run Gurobi optimization
#
# This script installs:
# - Python 3
# - pip and virtualenv
# - Gurobi optimizer
#
# Usage:
#   chmod +x setup_vm.sh
#   ./setup_vm.sh

set -e  # Exit on error

echo "========================================"
echo "Gurobi VM Setup Script"
echo "========================================"
echo ""

# Update system
echo "Updating system packages..."
sudo apt-get update -qq
sudo apt-get upgrade -y -qq

# Install Python and dependencies
echo "Installing Python 3 and pip..."
sudo apt-get install -y -qq python3 python3-pip python3-venv

# Install required system packages
echo "Installing system dependencies..."
sudo apt-get install -y -qq wget curl

# Create working directory
WORK_DIR="$HOME/gurobi_workspace"
echo "Creating workspace at $WORK_DIR..."
mkdir -p "$WORK_DIR"
cd "$WORK_DIR"

# Download and install Gurobi
GUROBI_VERSION="11.0.0"
GUROBI_SHORT="11.0"
GUROBI_DIR="gurobi${GUROBI_VERSION//./}"  # e.g., gurobi1100

echo "Downloading Gurobi ${GUROBI_VERSION}..."
wget -q "https://packages.gurobi.com/${GUROBI_SHORT}/gurobi${GUROBI_VERSION}_linux64.tar.gz"

echo "Extracting Gurobi..."
tar -xzf "gurobi${GUROBI_VERSION}_linux64.tar.gz"
rm "gurobi${GUROBI_VERSION}_linux64.tar.gz"

# Set up environment variables
GUROBI_HOME="$WORK_DIR/${GUROBI_DIR}/linux64"
echo "Setting up Gurobi environment..."

# Add to current session
export GUROBI_HOME="$GUROBI_HOME"
export PATH="${PATH}:${GUROBI_HOME}/bin"
export LD_LIBRARY_PATH="${LD_LIBRARY_PATH}:${GUROBI_HOME}/lib"

# Add to .bashrc for future sessions
cat >> "$HOME/.bashrc" << EOF

# Gurobi environment variables
export GUROBI_HOME="$GUROBI_HOME"
export PATH="\${PATH}:\${GUROBI_HOME}/bin"
export LD_LIBRARY_PATH="\${LD_LIBRARY_PATH}:\${GUROBI_HOME}/lib"
EOF

# Create Python virtual environment
echo "Creating Python virtual environment..."
python3 -m venv "$WORK_DIR/venv"
source "$WORK_DIR/venv/bin/activate"

# Install gurobipy and other packages
echo "Installing Gurobi Python package..."
pip install --quiet --upgrade pip
pip install --quiet gurobipy
echo "Installing additional Python packages..."
pip install --quiet numpy pandas

# Create convenience script to activate environment
cat > "$WORK_DIR/activate.sh" << 'EOF'
#!/bin/bash
# Convenience script to activate the Gurobi environment

source "$HOME/gurobi_workspace/venv/bin/activate"
export GUROBI_HOME="$HOME/gurobi_workspace/gurobi1100/linux64"
export PATH="${PATH}:${GUROBI_HOME}/bin"
export LD_LIBRARY_PATH="${LD_LIBRARY_PATH}:${GUROBI_HOME}/lib"

echo "Gurobi environment activated!"
echo "Python: $(which python3)"
echo "Workspace: $HOME/gurobi_workspace"
echo ""
echo "To set your Gurobi WLS license, run:"
echo "  export WLSACCESSID=\"your-access-id\""
echo "  export WLSSECRET=\"your-secret\""
echo "  export LICENSEID=\"your-license-id\""
EOF

chmod +x "$WORK_DIR/activate.sh"

# Create a script to upload and run user code
cat > "$WORK_DIR/run_optimization.sh" << 'EOF'
#!/bin/bash
# Script to run optimization code

set -e

# Activate environment
source "$HOME/gurobi_workspace/activate.sh"

# Create gurobi.lic file if WLS credentials are provided
if [ -n "$WLSACCESSID" ] && [ -n "$WLSSECRET" ] && [ -n "$LICENSEID" ]; then
    echo "Creating Gurobi WLS license file..."
    cat > "$HOME/gurobi.lic" << LICEOF
WLSACCESSID=$WLSACCESSID
WLSSECRET=$WLSSECRET
LICENSEID=$LICENSEID
LICEOF
    export GRB_LICENSE_FILE="$HOME/gurobi.lic"
    echo "✓ Gurobi WLS license configured"
    echo "Debug: License file created at $HOME/gurobi.lic"
    echo "Debug: LICENSEID = $LICENSEID"
    echo "Debug: WLSACCESSID length = ${#WLSACCESSID}"
    echo "Debug: WLSSECRET length = ${#WLSSECRET}"
else
    echo "WARNING: Gurobi WLS license variables not set!"
    echo "The restricted trial license will be used (limited model size)"
    echo ""
fi

# Run the optimization script
if [ -f "$HOME/gurobi_workspace/user_code.py" ]; then
    echo "Running optimization..."
    python3 "$HOME/gurobi_workspace/user_code.py"
else
    echo "No user code found at $HOME/gurobi_workspace/user_code.py"
    echo "Upload your Python script to this location and try again."
    exit 1
fi
EOF

chmod +x "$WORK_DIR/run_optimization.sh"

echo ""
echo "========================================"
echo "Setup Complete!"
echo "========================================"
echo ""
echo "Workspace location: $WORK_DIR"
echo "Gurobi version: ${GUROBI_VERSION}"
echo ""
echo "Quick start:"
echo "  1. Activate environment:"
echo "     source ~/gurobi_workspace/activate.sh"
echo ""
echo "  2. Set your Gurobi WLS license (if using WLS):"
echo "     export WLSACCESSID=\"your-access-id\""
echo "     export WLSSECRET=\"your-secret\""
echo "     export LICENSEID=\"your-license-id\""
echo ""
echo "  3. Upload your optimization script as:"
echo "     ~/gurobi_workspace/user_code.py"
echo ""
echo "  4. Run optimization:"
echo "     ~/gurobi_workspace/run_optimization.sh"
echo ""
echo "========================================"

# Test Gurobi installation
echo "Testing Gurobi installation..."
python3 -c "import gurobipy as gp; print(f'Gurobi version: {gp.gurobi.version()}'); print('✓ Gurobi installed successfully')" || echo "✗ Gurobi installation test failed"

echo ""
echo "Setup script finished!"
