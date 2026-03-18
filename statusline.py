#!/usr/bin/env python3
"""
Claude Code Statusline - A customizable status bar for Claude Code CLI
Reads JSON from stdin and outputs a formatted status line based on config.
"""

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

# Configuration file path
CONFIG_PATH = Path.home() / ".claude" / "statusline-config.json"

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
        "tokens": {}
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
    "bold": "\033[1m"
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
    """Render the pixel-style progress bar."""
    pb_config = config.get("progress_bar", {})
    width = pb_config.get("width", 10)
    filled_char = pb_config.get("filled_char", "█")
    empty_char = pb_config.get("empty_char", "░")
    gradient_char = pb_config.get("gradient_char", "▓")

    filled = int(percentage / 100 * width)
    remaining = width - filled

    # Add gradient character at the boundary if there's remaining space
    if remaining > 0 and filled > 0:
        bar = filled_char * (filled - 1) + gradient_char + empty_char * (remaining - 1)
    elif remaining > 0:
        bar = empty_char * remaining
    else:
        bar = filled_char * width

    color = get_color_for_percentage(percentage, config)
    reset = COLORS["reset"] if color else ""

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
    input_tokens = context.get("input_tokens", 0)
    output_tokens = context.get("output_tokens", 0)
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

    cost = data.get("cost", {}).get("total", 0)
    return fmt.format(cost=f"{cost:.4f}")


def render_duration(data: dict, config: dict) -> str:
    """Render session duration component."""
    duration_config = config.get("components", {}).get("duration", {})
    fmt = duration_config.get("format", "{duration}")

    duration_seconds = data.get("duration_seconds", 0)

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


def render_component(name: str, data: dict, config: dict) -> str:
    """Dispatch to the appropriate component renderer."""
    renderers = {
        "progress_bar": lambda: render_progress_bar(
            data.get("context_window", {}).get("used_percentage", 0),
            config
        ),
        "model": lambda: render_model(data, config),
        "directory": lambda: render_directory(data, config),
        "git": lambda: render_git(data, config),
        "tokens": lambda: render_tokens(data, config),
        "cost": lambda: render_cost(data, config),
        "duration": lambda: render_duration(data, config),
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
