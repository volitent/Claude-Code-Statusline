#!/bin/bash

# Claude Code Statusline Installer
# This script installs the statusline for Claude Code CLI

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLAUDE_DIR="$HOME/.claude"
STATUSLINE_SCRIPT="$CLAUDE_DIR/statusline.py"
CONFIG_FILE="$CLAUDE_DIR/statusline-config.json"
SETTINGS_FILE="$CLAUDE_DIR/settings.json"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_python() {
    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
    elif command -v python &> /dev/null; then
        PYTHON_CMD="python"
    else
        print_error "Python is not installed. Please install Python 3.x to continue."
        exit 1
    fi

    # Check Python version
    PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | awk '{print $2}')
    print_info "Found Python $PYTHON_VERSION"
}

install() {
    print_info "Installing Claude Code Statusline..."

    # Check Python
    check_python

    # Create .claude directory if it doesn't exist
    if [ ! -d "$CLAUDE_DIR" ]; then
        mkdir -p "$CLAUDE_DIR"
        print_info "Created $CLAUDE_DIR"
    fi

    # Copy statusline script
    if [ -f "$STATUSLINE_SCRIPT" ]; then
        print_warning "Existing statusline.py found, creating backup..."
        cp "$STATUSLINE_SCRIPT" "$STATUSLINE_SCRIPT.backup"
    fi

    cp "$SCRIPT_DIR/statusline.py" "$STATUSLINE_SCRIPT"
    chmod +x "$STATUSLINE_SCRIPT"
    print_success "Installed statusline.py to $CLAUDE_DIR"

    # Create default config if it doesn't exist
    if [ ! -f "$CONFIG_FILE" ]; then
        if [ -f "$SCRIPT_DIR/config.json" ]; then
            cp "$SCRIPT_DIR/config.json" "$CONFIG_FILE"
            print_success "Created default configuration at $CONFIG_FILE"
        else
            print_warning "config.json not found in script directory, skipping config installation"
        fi
    else
        print_info "Configuration file already exists at $CONFIG_FILE (preserving)"
    fi

    # Update settings.json
    update_settings

    print_success "Installation complete!"
    echo ""
    echo "To test your statusline, run:"
    echo "  echo '{\"model\":{\"display_name\":\"Opus\"},\"context_window\":{\"used_percentage\":45}}' | $PYTHON_CMD $STATUSLINE_SCRIPT"
    echo ""
    echo "Configuration file: $CONFIG_FILE"
    echo "Restart Claude Code to see your new statusline!"
}

update_settings() {
    print_info "Updating Claude Code settings..."

    # Create settings.json if it doesn't exist
    if [ ! -f "$SETTINGS_FILE" ]; then
        echo '{}' > "$SETTINGS_FILE"
        print_info "Created $SETTINGS_FILE"
    fi

    # Check if statusLine already exists
    if grep -q '"statusLine"' "$SETTINGS_FILE" 2>/dev/null; then
        print_warning "statusLine configuration already exists in settings.json"
        read -p "Do you want to overwrite it? (y/N) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_info "Skipping settings.json update"
            return
        fi
    fi

    # Create a backup
    cp "$SETTINGS_FILE" "$SETTINGS_FILE.backup"

    # Update settings.json with statusLine configuration
    # Using Python for reliable JSON manipulation
    $PYTHON_CMD << 'EOF'
import json
import os

settings_path = os.path.expanduser("~/.claude/settings.json")

try:
    with open(settings_path, "r") as f:
        settings = json.load(f)
except (json.JSONDecodeError, FileNotFoundError):
    settings = {}

# Add statusLine configuration
settings["statusLine"] = {
    "command": f"python3 {os.path.expanduser('~/.claude/statusline.py')}"
}

# Write back
with open(settings_path, "w") as f:
    json.dump(settings, f, indent=2)

print("Updated settings.json with statusLine configuration")
EOF

    print_success "Updated $SETTINGS_FILE"
}

uninstall() {
    print_info "Uninstalling Claude Code Statusline..."

    # Remove statusline script
    if [ -f "$STATUSLINE_SCRIPT" ]; then
        rm "$STATUSLINE_SCRIPT"
        print_success "Removed statusline.py"
    else
        print_info "statusline.py not found, skipping"
    fi

    # Ask about config file
    if [ -f "$CONFIG_FILE" ]; then
        read -p "Do you want to keep your configuration file? (Y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Nn]$ ]]; then
            # Create backup
            cp "$CONFIG_FILE" "$CONFIG_FILE.backup"
            print_info "Configuration backed up to $CONFIG_FILE.backup"
        fi
        rm "$CONFIG_FILE"
        print_success "Removed configuration file"
    fi

    # Update settings.json to remove statusLine
    if [ -f "$SETTINGS_FILE" ]; then
        $PYTHON_CMD << 'EOF'
import json
import os

settings_path = os.path.expanduser("~/.claude/settings.json")

try:
    with open(settings_path, "r") as f:
        settings = json.load(f)

    if "statusLine" in settings:
        del settings["statusLine"]

        with open(settings_path, "w") as f:
            json.dump(settings, f, indent=2)

        print("Removed statusLine from settings.json")
    else:
        print("No statusLine configuration found in settings.json")
except (json.JSONDecodeError, FileNotFoundError) as e:
    print(f"Warning: Could not update settings.json: {e}")
EOF
        print_success "Cleaned up settings.json"
    fi

    # Remove backup files
    for backup in "$STATUSLINE_SCRIPT.backup" "$SETTINGS_FILE.backup"; do
        if [ -f "$backup" ]; then
            rm "$backup"
            print_info "Removed backup: $backup"
        fi
    done

    print_success "Uninstallation complete!"
}

show_help() {
    echo "Claude Code Statusline Installer"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --install, -i     Install the statusline (default)"
    echo "  --uninstall, -u   Uninstall the statusline"
    echo "  --help, -h        Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                # Install statusline"
    echo "  $0 --install      # Install statusline"
    echo "  $0 --uninstall    # Uninstall statusline"
}

# Main entry point
case "${1:-}" in
    --uninstall|-u)
        uninstall
        ;;
    --help|-h)
        show_help
        ;;
    --install|-i|"")
        install
        ;;
    *)
        print_error "Unknown option: $1"
        show_help
        exit 1
        ;;
esac
