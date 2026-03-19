#!/usr/bin/env python3
"""
Claude Code Statusline - A customizable status bar for Claude Code CLI
Reads JSON from stdin and outputs a formatted status line based on config.
"""

import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

# Configuration file path
CONFIG_PATH = Path.home() / ".claude" / "statusline-config.json"

# Usage data cache
USAGE_CACHE_DIR = Path.home() / ".cache" / "ccstatusline"
USAGE_CACHE_FILE = USAGE_CACHE_DIR / "usage.json"
USAGE_CACHE_MAX_AGE = 180  # seconds

# Default configuration
DEFAULT_CONFIG = {
    "lines": [
        {
            "components": ["model", "directory", "git"],
            "separator": " | "
        },
        {
            "components": ["progress_bar", "tokens", "cost"],
            "separator": " "
        }
    ],
    "progress_bar": {
        "width": 10,
        "filled_char": "█",
        "empty_char": "░",
        "gradient_char": "▓"
    },
    "colors": {
        "enabled": True,
        "low": {"threshold": 50, "color": "green"},
        "medium": {"threshold": 75, "color": "yellow"},
        "high": {"threshold": 90, "color": "red"}
    },
    "tokens": {
        "format": "in:{input} out:{output} total:{total}",
        "unit": "k"
    },
    "components": {
        "model": {"format": "{name}"},
        "directory": {"max_length": 20, "show_git_root": True},
        "git": {"show_branch": True, "show_changes": True},
        "cost": {"format": "${cost}"},
        "duration": {"format": "{duration}"},
        "progress_bar": {},
        "tokens": {},
        "version": {"format": "v{version}"},
        "tokens_cached": {"format": "cached:{cached}"},
        "lines_changed": {"format": "+{added} -{removed}"},
        "custom_text": {"text": ""},
        "weekly_usage": {"format": "Weekly: {percent:.1f}%"},
        "block_timer": {"format": "Block: {elapsed}", "show_progress": False}
    }
}

# ANSI color codes
COLORS = {
    "reset": "\033[0m",
    "green": "\033[32m",
    "yellow": "\033[33m",
    "orange": "\033[38;5;208m",
    "red": "\033[31m",
    "blue": "\033[34m",
    "cyan": "\033[36m",
    "magenta": "\033[35m",
    "dim": "\033[2m",
    "bold": "\033[1m",
    "bright_blue": "\033[94m",
    "gray": "\033[90m"
}


def load_config() -> dict:
    """Load configuration from file or return defaults."""
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                user_config = json.load(f)
            # Merge with defaults
            return merge_config(DEFAULT_CONFIG, user_config)
        except (json.JSONDecodeError, IOError):
            pass
    return DEFAULT_CONFIG


def merge_config(base: dict, override: dict) -> dict:
    """Recursively merge override config into base config."""
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_config(result[key], value)
        else:
            result[key] = value
    return result


def get_color_for_percentage(percentage: float, config: dict) -> str:
    """Get the appropriate color based on context usage percentage."""
    colors_config = config.get("colors", {})
    if not colors_config.get("enabled", True):
        return ""

    low = colors_config.get("low", {"threshold": 50, "color": "green"})
    medium = colors_config.get("medium", {"threshold": 75, "color": "yellow"})
    high = colors_config.get("high", {"threshold": 90, "color": "red"})

    if percentage < low["threshold"]:
        return COLORS.get(low["color"], "")
    elif percentage < medium["threshold"]:
        return COLORS.get(medium["color"], "")
    elif percentage < high["threshold"]:
        return COLORS.get("orange", COLORS.get(high["color"], ""))
    else:
        return COLORS.get(high["color"], "")


def format_tokens(value: int, unit: str) -> str:
    """Format token count with appropriate unit."""
    if unit == "k":
        return f"{value / 1000:.1f}k"
    elif unit == "m":
        return f"{value / 1_000_000:.2f}m"
    elif unit == "auto":
        if value >= 1_000_000:
            return f"{value / 1_000_000:.2f}m"
        elif value >= 1000:
            return f"{value / 1000:.1f}k"
        return str(value)
    return str(value)


def render_progress_bar(percentage: float, config: dict) -> str:
    """Render the pixel-style progress bar with percentage."""
    pb_config = config.get("progress_bar", {})
    width = pb_config.get("width", 10)
    filled_char = pb_config.get("filled_char", "█")
    empty_char = pb_config.get("empty_char", "░")
    show_percentage = pb_config.get("show_percentage", True)

    # Handle null/None values
    percentage = percentage or 0

    filled = int(percentage / 100 * width)
    remaining = width - filled

    # Simple progress bar without gradient
    bar = filled_char * filled + empty_char * remaining

    color = get_color_for_percentage(percentage, config)
    reset = COLORS["reset"] if color else ""

    # Add percentage number after the bar
    if show_percentage:
        pct_display = int(percentage)
        return f"{color}{bar}{reset} {color}{pct_display}%{reset}"
    else:
        return f"{color}{bar}{reset}"


def render_model(data: dict, config: dict) -> str:
    """Render model name component."""
    model_data = data.get("model", {})
    model_config = config.get("components", {}).get("model", {})
    fmt = model_config.get("format", "{name}")

    name = model_data.get("display_name", model_data.get("name", "Unknown"))
    return fmt.format(name=name)


def render_directory(data: dict, config: dict) -> str:
    """Render current directory component."""
    dir_config = config.get("components", {}).get("directory", {})
    max_length = dir_config.get("max_length", 20)
    show_git_root = dir_config.get("show_git_root", True)

    cwd = os.getcwd()
    home = str(Path.home())

    # Try to get git root if enabled
    if show_git_root:
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--show-toplevel"],
                capture_output=True,
                text=True,
                cwd=cwd
            )
            if result.returncode == 0:
                git_root = result.stdout.strip()
                cwd = git_root
        except (subprocess.SubprocessError, FileNotFoundError):
            pass

    # Shorten path
    if cwd.startswith(home):
        cwd = "~" + cwd[len(home):]

    if len(cwd) > max_length:
        parts = cwd.split("/")
        shortened = []
        for part in parts:
            if len("/".join(shortened + [part])) > max_length - 3:
                break
            shortened.append(part)
        cwd = "/".join(shortened) + "..."

    return cwd


def render_git(data: dict, config: dict) -> str:
    """Render git information component."""
    git_config = config.get("components", {}).get("git", {})
    show_branch = git_config.get("show_branch", True)
    show_changes = git_config.get("show_changes", True)

    parts = []

    try:
        # Get branch name
        if show_branch:
            result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                branch = result.stdout.strip()
                parts.append(f"{COLORS['cyan']}{branch}{COLORS['reset']}")

        # Get changes count
        if show_changes:
            # Staged changes
            result = subprocess.run(
                ["git", "diff", "--cached", "--numstat"],
                capture_output=True,
                text=True
            )
            staged = len(result.stdout.strip().split("\n")) if result.stdout.strip() else 0

            # Unstaged changes
            result = subprocess.run(
                ["git", "diff", "--numstat"],
                capture_output=True,
                text=True
            )
            unstaged = len(result.stdout.strip().split("\n")) if result.stdout.strip() else 0

            if staged > 0 or unstaged > 0:
                changes = []
                if staged > 0:
                    changes.append(f"{COLORS['green']}+{staged}{COLORS['reset']}")
                if unstaged > 0:
                    changes.append(f"{COLORS['red']}~{unstaged}{COLORS['reset']}")
                parts.append("[".join(changes) + "]" if len(changes) > 1 else changes[0])

    except (subprocess.SubprocessError, FileNotFoundError):
        pass

    return " ".join(parts) if parts else ""


def render_tokens(data: dict, config: dict) -> str:
    """Render token statistics component."""
    tokens_config = config.get("tokens", {})
    fmt = tokens_config.get("format", "in:{input} out:{output} total:{total}")
    unit = tokens_config.get("unit", "k")

    context = data.get("context_window", {})
    # Use correct field names from Claude Code JSON
    input_tokens = context.get("total_input_tokens", 0) or 0
    output_tokens = context.get("total_output_tokens", 0) or 0
    total = input_tokens + output_tokens

    return fmt.format(
        input=format_tokens(input_tokens, unit),
        output=format_tokens(output_tokens, unit),
        total=format_tokens(total, unit)
    )


def render_cost(data: dict, config: dict) -> str:
    """Render session cost component."""
    cost_config = config.get("components", {}).get("cost", {})
    fmt = cost_config.get("format", "${cost}")

    # Use correct field name from Claude Code JSON
    cost = data.get("cost", {}).get("total_cost_usd", 0) or 0
    return fmt.format(cost=f"{cost:.4f}")


def render_duration(data: dict, config: dict) -> str:
    """Render session duration component."""
    duration_config = config.get("components", {}).get("duration", {})
    fmt = duration_config.get("format", "{duration}")

    # Use correct field name: total_duration_ms (milliseconds)
    duration_ms = data.get("cost", {}).get("total_duration_ms", 0) or 0
    duration_seconds = duration_ms // 1000

    if duration_seconds < 60:
        duration = f"{int(duration_seconds)}s"
    elif duration_seconds < 3600:
        minutes = int(duration_seconds / 60)
        seconds = int(duration_seconds % 60)
        duration = f"{minutes}m{seconds}s"
    else:
        hours = int(duration_seconds / 3600)
        minutes = int((duration_seconds % 3600) / 60)
        duration = f"{hours}h{minutes}m"

    return fmt.format(duration=duration)


def get_context_percentage(data: dict) -> float:
    """Get context usage percentage, with fallback calculation if needed."""
    context = data.get("context_window", {})

    # Try to use precomputed percentage first
    percentage = context.get("used_percentage")
    if percentage is not None:
        return percentage

    # Fallback: calculate from total_input_tokens and context_window_size
    total_input = context.get("total_input_tokens", 0) or 0
    window_size = context.get("context_window_size", 200000) or 200000

    if total_input > 0 and window_size > 0:
        return (total_input / window_size) * 100

    return 0


# ============================================================
# NEW COMPONENTS
# ============================================================

def render_version(data: dict, config: dict) -> str:
    """Render Claude Code version component."""
    version_config = config.get("components", {}).get("version", {})
    fmt = version_config.get("format", "v{version}")

    version = data.get("version", "")
    if version:
        return fmt.format(version=version)
    return ""


def render_tokens_cached(data: dict, config: dict) -> str:
    """Render cached tokens component."""
    cached_config = config.get("components", {}).get("tokens_cached", {})
    fmt = cached_config.get("format", "cached:{cached}")
    unit = cached_config.get("unit", "k")

    context = data.get("context_window", {})

    # Get cached tokens from current_usage
    current_usage = context.get("current_usage", {})
    cache_creation = 0
    cache_read = 0

    if isinstance(current_usage, dict):
        cache_creation = current_usage.get("cache_creation_input_tokens", 0) or 0
        cache_read = current_usage.get("cache_read_input_tokens", 0) or 0

    total_cached = cache_creation + cache_read

    if total_cached > 0:
        return fmt.format(cached=format_tokens(total_cached, unit))
    return ""


def render_lines_changed(data: dict, config: dict) -> str:
    """Render lines changed component (added/removed)."""
    lines_config = config.get("components", {}).get("lines_changed", {})
    fmt = lines_config.get("format", "+{added} -{removed}")

    cost_data = data.get("cost", {})
    lines_added = cost_data.get("total_lines_added", 0) or 0
    lines_removed = cost_data.get("total_lines_removed", 0) or 0

    if lines_added > 0 or lines_removed > 0:
        color = COLORS.get("cyan", "")
        reset = COLORS["reset"] if color else ""
        result = fmt.format(added=lines_added, removed=lines_removed)
        return f"{color}{result}{reset}"
    return ""


def render_custom_text(data: dict, config: dict) -> str:
    """Render custom text component."""
    custom_config = config.get("components", {}).get("custom_text", {})
    text = custom_config.get("text", "")
    color = custom_config.get("color", "")

    if text:
        if color and color in COLORS:
            return f"{COLORS[color]}{text}{COLORS['reset']}"
        return text
    return ""


def _fetch_usage_data() -> Optional[dict]:
    """
    Fetch usage data from Anthropic API.
    Returns dict with session_usage, weekly_usage, session_reset_at, weekly_reset_at.
    """
    try:
        # Try to get cached data first
        if USAGE_CACHE_FILE.exists():
            cache_age = time.time() - USAGE_CACHE_FILE.stat().st_mtime
            if cache_age < USAGE_CACHE_MAX_AGE:
                with open(USAGE_CACHE_FILE, "r") as f:
                    return json.load(f)

        # Try to read credentials
        token = _get_usage_token()
        if not token:
            return None

        # Make API request
        import urllib.request
        import urllib.error

        req = urllib.request.Request(
            "https://api.anthropic.com/api/oauth/usage",
            headers={
                "Authorization": f"Bearer {token}",
                "anthropic-beta": "oauth-2025-04-20"
            }
        )

        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())

            result = {
                "session_usage": data.get("five_hour", {}).get("utilization"),
                "session_reset_at": data.get("five_hour", {}).get("resets_at"),
                "weekly_usage": data.get("seven_day", {}).get("utilization"),
                "weekly_reset_at": data.get("seven_day", {}).get("resets_at")
            }

            # Cache the result
            USAGE_CACHE_DIR.mkdir(parents=True, exist_ok=True)
            with open(USAGE_CACHE_FILE, "w") as f:
                json.dump(result, f)

            return result

    except Exception:
        return None


def _get_usage_token() -> Optional[str]:
    """Get usage API token from credentials file or keychain."""
    try:
        # Try credentials file first
        cred_file = Path.home() / ".claude" / ".credentials.json"
        if cred_file.exists():
            with open(cred_file, "r") as f:
                data = json.load(f)
                return data.get("claudeAiOauth", {}).get("accessToken")

        # On macOS, try keychain
        if sys.platform == "darwin":
            result = subprocess.run(
                ["security", "find-generic-password", "-s", "Claude Code-credentials", "-w"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                secret = result.stdout.strip()
                data = json.loads(secret)
                return data.get("claudeAiOauth", {}).get("accessToken")
    except Exception:
        pass

    return None


def render_weekly_usage(data: dict, config: dict) -> str:
    """Render weekly usage percentage component."""
    usage_config = config.get("components", {}).get("weekly_usage", {})
    fmt = usage_config.get("format", "Weekly: {percent:.1f}%")
    show_progress = usage_config.get("show_progress", False)

    usage_data = _fetch_usage_data()

    if usage_data and usage_data.get("weekly_usage") is not None:
        percent = usage_data["weekly_usage"]
        color = get_color_for_percentage(percent, config)
        reset = COLORS["reset"] if color else ""

        if show_progress:
            bar = _make_progress_bar(percent, 8)
            return f"{color}{fmt.format(percent=percent)} {bar}{reset}"

        return f"{color}{fmt.format(percent=percent)}{reset}"

    return ""


def render_block_timer(data: dict, config: dict) -> str:
    """Render 5-hour block timer component."""
    timer_config = config.get("components", {}).get("block_timer", {})
    fmt = timer_config.get("format", "Block: {elapsed}")
    show_progress = timer_config.get("show_progress", False)
    show_remaining = timer_config.get("show_remaining", False)

    usage_data = _fetch_usage_data()

    if usage_data and usage_data.get("session_reset_at"):
        try:
            reset_at = usage_data["session_reset_at"]
            # Parse ISO format timestamp
            reset_time = datetime.fromisoformat(reset_at.replace("Z", "+00:00"))
            now = datetime.now(timezone.utc)

            # Calculate elapsed time (5 hour block = 18000 seconds)
            total_block_ms = 5 * 60 * 60 * 1000  # 5 hours in ms
            remaining_ms = int((reset_time - now).total_seconds() * 1000)
            elapsed_ms = total_block_ms - remaining_ms

            if elapsed_ms < 0:
                elapsed_ms = 0
            if remaining_ms < 0:
                remaining_ms = 0

            # Format elapsed time
            elapsed_hours = int(elapsed_ms // (1000 * 60 * 60))
            elapsed_minutes = int((elapsed_ms % (1000 * 60 * 60)) // (1000 * 60))

            if show_remaining:
                remaining_hours = int(remaining_ms // (1000 * 60 * 60))
                remaining_minutes = int((remaining_ms % (1000 * 60 * 60)) // (1000 * 60))
                elapsed_str = f"{remaining_hours}h{remaining_minutes}m remaining"
            else:
                elapsed_str = f"{elapsed_hours}h{elapsed_minutes}m"

            # Calculate percentage
            percent = (elapsed_ms / total_block_ms) * 100 if total_block_ms > 0 else 0
            color = get_color_for_percentage(percent, config)
            reset = COLORS["reset"] if color else ""

            if show_progress:
                bar = _make_progress_bar(percent, 8)
                return f"{color}{fmt.format(elapsed=elapsed_str)} {bar}{reset}"

            return f"{color}{fmt.format(elapsed=elapsed_str)}{reset}"

        except Exception:
            pass

    return ""


def _make_progress_bar(percent: float, width: int = 10) -> str:
    """Make a simple progress bar."""
    filled = int(percent / 100 * width)
    remaining = width - filled
    return "█" * filled + "░" * remaining


def render_component(name: str, data: dict, config: dict) -> str:
    """Dispatch to the appropriate component renderer."""
    renderers = {
        "progress_bar": lambda: render_progress_bar(
            get_context_percentage(data),
            config
        ),
        "model": lambda: render_model(data, config),
        "directory": lambda: render_directory(data, config),
        "git": lambda: render_git(data, config),
        "tokens": lambda: render_tokens(data, config),
        "cost": lambda: render_cost(data, config),
        "duration": lambda: render_duration(data, config),
        # New components
        "version": lambda: render_version(data, config),
        "tokens_cached": lambda: render_tokens_cached(data, config),
        "lines_changed": lambda: render_lines_changed(data, config),
        "custom_text": lambda: render_custom_text(data, config),
        "weekly_usage": lambda: render_weekly_usage(data, config),
        "block_timer": lambda: render_block_timer(data, config),
    }

    renderer = renderers.get(name)
    if renderer:
        return renderer()
    return ""


def render_statusline(data: dict, config: dict) -> str:
    """Render the complete statusline based on configuration."""
    lines = config.get("lines", [])
    output_lines = []

    for line_config in lines:
        components = line_config.get("components", [])
        separator = line_config.get("separator", " ")

        rendered = []
        for comp_name in components:
            result = render_component(comp_name, data, config)
            if result:
                rendered.append(result)

        if rendered:
            output_lines.append(separator.join(rendered))

    return "\n".join(output_lines)


def main():
    """Main entry point."""
    # Read JSON from stdin
    try:
        input_data = sys.stdin.read()
        if not input_data.strip():
            # No input, show minimal status
            print("")
            return

        data = json.loads(input_data)
    except json.JSONDecodeError as e:
        print(f"Statusline error: Invalid JSON input", file=sys.stderr)
        sys.exit(1)

    # Load configuration
    config = load_config()

    # Render and output
    status = render_statusline(data, config)
    print(status)


if __name__ == "__main__":
    main()
