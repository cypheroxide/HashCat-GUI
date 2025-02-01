#!/bin/bash

# Color definitions
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Error handling
set -e
trap 'last_command=$current_command; current_command=$BASH_COMMAND' DEBUG
trap 'echo -e "${RED}ERROR: Command \"${last_command}\" failed with exit code $?${NC}"; exit 1' ERR

# Function to print status messages
print_status() {
    echo -e "${BLUE}[*] $1${NC}"
}

print_success() {
    echo -e "${GREEN}[+] $1${NC}"
}

print_error() {
    echo -e "${RED}[-] $1${NC}" >&2
}

print_warning() {
    echo -e "${YELLOW}[!] $1${NC}"
}

# Check for required dependencies
check_dependency() {
    if ! command -v "$1" &> /dev/null; then
        print_error "$1 is required but not installed."
        return 1
    fi
}

# Check core dependencies
print_status "Checking dependencies..."
for dep in python3 pip hashcat; do
    check_dependency "$dep" || missing_deps=1
done

if [ "$missing_deps" = "1" ]; then
    print_warning "Please install missing dependencies using your package manager"
    print_warning "For Debian/Ubuntu: sudo apt install python3 python3-pip hashcat"
    print_warning "For Arch Linux: sudo pacman -S python python-pip hashcat"
    exit 1
fi

# Detect Linux distribution
print_status "Detecting Linux distribution..."
if [ -f /etc/debian_version ]; then
    DISTRO="debian"
    print_success "Detected Debian-based distribution"
    
    # Update package lists
    print_status "Updating package lists..."
    apt-get update

    # Install system dependencies
    print_status "Installing system dependencies..."
    apt-get install -y \
        python3 \
        python3-pip \
        python3-venv \
        python3-qt5 \
        git \
        hashcat \
        python3-dev \
        build-essential \
        libssl-dev \
        libffi-dev \
        libjpeg-dev \
        zlib1g-dev \
        wordlists
    
elif [ -f /etc/arch-release ]; then
    DISTRO="arch"
    print_success "Detected Arch-based distribution"
    
    # Update system
    print_status "Updating system..."
    pacman -Syu --noconfirm

    # Install system dependencies
    print_status "Installing system dependencies..."
    pacman -S --noconfirm \
        python \
        python-pip \
        python-virtualenv \
        python-pyqt5 \
        git \
        hashcat \
        base-devel \
        openssl \
        zlib \
        wordlists
else
    print_error "Unsupported Linux distribution"
    exit 1
fi

# Define directories
APP_NAME="hashcat-gui"
PROJECT_DIR="$(pwd)"
LOCAL_DIR="$HOME/.local"
INSTALL_DIR="$LOCAL_DIR/lib/$APP_NAME"
DATA_DIR="$LOCAL_DIR/share/$APP_NAME"
CONFIG_DIR="$HOME/.config/$APP_NAME"
BIN_DIR="$LOCAL_DIR/bin"
SYSTEMD_DIR="$HOME/.config/systemd/user"
DESKTOP_DIR="$LOCAL_DIR/share/applications"

# Create directories
print_status "Creating directories..."
mkdir -p "$INSTALL_DIR"
mkdir -p "$DATA_DIR"
mkdir -p "$CONFIG_DIR"
mkdir -p "$BIN_DIR"
mkdir -p "$SYSTEMD_DIR"
mkdir -p "$DESKTOP_DIR"
mkdir -p ~/.hashcat/{rules,masks}

# Copy application files
print_status "Installing application files..."
cp -r src/* "$INSTALL_DIR/"
cp -r data/* "$DATA_DIR/"
cp src/core/config.json "$CONFIG_DIR/"

# Install desktop entry
print_status "Installing desktop entry..."
cat > "$DESKTOP_DIR/$APP_NAME.desktop" << EOF
[Desktop Entry]
Version=1.0
Name=HashCat GUI
Comment=Advanced Password Recovery Tool
Exec=/usr/local/bin/$APP_NAME
Icon=$APP_NAME
Terminal=false
Type=Application
Categories=Security;System;Utility;
Keywords=hash;password;cracking;security;
EOF

# Install systemd service
print_status "Installing systemd service..."
cat > "$SYSTEMD_DIR/$APP_NAME.service" << EOF
[Unit]
Description=HashCat GUI Password Recovery Service
After=network.target

[Service]
Type=simple
User=root
ExecStart=/usr/local/bin/$APP_NAME --service
Restart=on-failure
RestartSec=5
StandardOutput=syslog
StandardError=syslog
SyslogIdentifier=$APP_NAME

[Install]
WantedBy=multi-user.target
EOF

# Install Python dependencies
print_status "Installing Python dependencies..."
python3 -m pip install --user --upgrade pip
python3 -m pip install --user -r requirements.txt

# Set permissions
# Set permissions
print_status "Setting permissions..."
chmod -R u+rw "$INSTALL_DIR"
chmod -R u+rw "$DATA_DIR"
chmod -R u+rw "$CONFIG_DIR"
chmod u+x "$BIN_DIR/$APP_NAME"
chmod 644 "$DESKTOP_DIR/$APP_NAME.desktop"
chmod 644 "$SYSTEMD_DIR/$APP_NAME.service"

# Create launcher script
# Create launcher script
print_status "Creating launcher script..."
cat > "$BIN_DIR/$APP_NAME" << EOF
#!/bin/bash
exec python3 "$INSTALL_DIR/core/server.py" "\$@"
EOF
chmod u+x "$BIN_DIR/$APP_NAME"

# Reload systemd and enable user service
print_status "Configuring user service..."
systemctl --user daemon-reload
systemctl --user enable "$APP_NAME.service"
systemctl --user start "$APP_NAME.service"

print_success "Installation completed successfully!"
echo -e "${GREEN}Services started and enabled:${NC}"
echo -e "  - $APP_NAME.service"
echo -e "\n${GREEN}You can now:${NC}"
echo -e "1. Start the GUI by running: $APP_NAME"
echo -e "2. Launch from your application menu"
echo -e "3. Check service status: systemctl status $APP_NAME"
echo -e "\n${YELLOW}Note: The service is running as root for hashcat compatibility${NC}"
