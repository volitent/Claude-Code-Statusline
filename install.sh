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
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
BOLD='\033[1m'
DIM='\033[2m'
NC='\033[0m'

# Default options
LINE_COUNT=2
LINE1_COMPONENTS=""
LINE2_COMPONENTS=""
LINE3_COMPONENTS=""
TOKEN_IN=true
TOKEN_OUT=true
TOKEN_TOTAL=true
OPT_QUICK=false

print_info() { echo -e "${BLUE}ℹ️${NC} $1"; }
print_success() { echo -e "${GREEN}✅${NC} $1"; }
print_warning() { echo -e "${YELLOW}⚠️${NC} $1"; }
print_error() { echo -e "${RED}❌${NC} $1"; }

clear_screen() { clear; }

print_header() {
    clear_screen
    echo -e "${BOLD}${CYAN}"
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║     🚀 Claude Code Statusline 安装配置工具 ✨              ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    echo ""
}

check_python() {
    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
    elif command -v python &> /dev/null; then
        PYTHON_CMD="python"
    else
        print_error "🐍 未找到 Python，请先安装 Python 3.x"
        exit 1
    fi
    PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | awk '{print $2}')
    print_info "检测到 Python $PYTHON_VERSION 🐍"
}

# 可用组件定义 - 分类显示
show_components() {
    echo -e "${BOLD}📋 可用组件：${NC}"
    echo ""

    echo -e "  ${CYAN}── 🎯 核心信息 ──${NC}"
    echo -e "  ${CYAN}1${NC}) 🤖 模型名称 (model)"
    echo -e "  ${CYAN}2${NC}) 📌 版本号 (version)"
    echo -e "  ${CYAN}3${NC}) 📁 当前目录 (directory)"
    echo -e "  ${CYAN}4${NC}) 🔧 Git 信息 (git)"

    echo ""
    echo -e "  ${CYAN}── 📊 Token & 上下文 ──${NC}"
    echo -e "  ${CYAN}5${NC}) 📈 进度条 (progress_bar)"
    echo -e "  ${CYAN}6${NC}) 🔢 Token 统计 (tokens)"
    echo -e "  ${CYAN}7${NC}) 💾 缓存 Token (tokens_cached)"

    echo ""
    echo -e "  ${CYAN}── ⏱️ 会话信息 ──${NC}"
    echo -e "  ${CYAN}8${NC}) 💰 会话费用 (cost)"
    echo -e "  ${CYAN}9${NC}) ⏳ 会话时长 (duration)"
    echo -e "  ${CYAN}10${NC}) 📝 代码行变化 (lines_changed)"

    echo ""
    echo -e "  ${CYAN}── 📆 使用量统计 ──${NC}"
    echo -e "  ${CYAN}11${NC}) 📅 周使用量 (weekly_usage) ${DIM}(需 API)${NC}"
    echo -e "  ${CYAN}12${NC}) 🕐 区块计时 (block_timer) ${DIM}(需 API)${NC}"

    echo ""
    echo -e "  ${CYAN}── ✏️ 自定义 ──${NC}"
    echo -e "  ${CYAN}13${NC}) 💬 自定义文本 (custom_text)"

    echo ""
    echo -e "${DIM}💡 提示：输入多个编号用空格分隔，例如: 1 3 4${NC}"
}

# 解析组件编号为组件名称
parse_component_num() {
    case "$1" in
        1) echo "model" ;;
        2) echo "version" ;;
        3) echo "directory" ;;
        4) echo "git" ;;
        5) echo "progress_bar" ;;
        6) echo "tokens" ;;
        7) echo "tokens_cached" ;;
        8) echo "cost" ;;
        9) echo "duration" ;;
        10) echo "lines_changed" ;;
        11) echo "weekly_usage" ;;
        12) echo "block_timer" ;;
        13) echo "custom_text" ;;
    esac
}

# 将编号列表转换为组件名称列表
parse_components() {
    local input="$1"
    local result=""

    for num in $input; do
        comp=$(parse_component_num "$num")
        if [ -n "$comp" ]; then
            if [ -n "$result" ]; then
                result="$result $comp"
            else
                result="$comp"
            fi
        fi
    done

    echo "$result"
}

# 格式化组件显示
format_components_display() {
    local comps="$1"
    local result=""

    for comp in $comps; do
        case "$comp" in
            model) result="$result 模型" ;;
            version) result="$result 版本" ;;
            directory) result="$result 目录" ;;
            git) result="$result Git" ;;
            progress_bar) result="$result 进度条" ;;
            tokens) result="$result Token" ;;
            tokens_cached) result="$result 缓存" ;;
            cost) result="$result 费用" ;;
            duration) result="$result 时长" ;;
            lines_changed) result="$result 行变化" ;;
            weekly_usage) result="$result 周使用" ;;
            block_timer) result="$result 区块计时" ;;
            custom_text) result="$result 自定义" ;;
        esac
    done
    echo "$result"
}

prompt_line_count() {
    while true; do
        print_header
        echo -e "${BOLD}📝 Step 1/4: 选择状态栏行数${NC}"
        echo ""
        echo -e "  ${CYAN}1${NC}) 📏 单行模式 - 所有组件在一行显示"
        echo -e "  ${CYAN}2${NC}) 📐 双行模式 - 组件分布在两行显示"
        echo -e "  ${CYAN}3${NC}) 📊 三行模式 - 组件分布在三行显示"
        echo ""
        read -p "请选择 [1/2/3，默认 2]: " choice

        case "$choice" in
            3) LINE_COUNT=3; return ;;
            2) LINE_COUNT=2; return ;;
            ""|1) LINE_COUNT=1; return ;;
            *) echo -e "${RED}❌ 无效选择，请输入 1、2 或 3${NC}"; sleep 1 ;;
        esac
    done
}

prompt_line_components() {
    local line_num="$1"

    while true; do
        print_header
        echo -e "${BOLD}🎨 Step $((line_num + 1))/4: 配置第 $line_num 行组件${NC}"
        echo ""
        show_components

        # 根据行号设置默认值
        local default_hint=""
        local default_nums=""
        case $line_num in
            1)
                default_hint="1 3 4 (模型 目录 Git)"
                default_nums="1 3 4"
                ;;
            2)
                default_hint="5 6 9 (进度条 Token 费用)"
                default_nums="5 6 9"
                ;;
            3)
                default_hint="10 11 (时长 行变化)"
                default_nums="10 11"
                ;;
        esac

        echo -e "${DIM}💡 留空使用默认: $default_hint${NC}"
        echo ""
        read -p "第 $line_num 行组件: " input

        if [ -z "$input" ]; then
            # 使用默认值
            case $line_num in
                1) LINE1_COMPONENTS="model directory git" ;;
                2) LINE2_COMPONENTS="progress_bar tokens cost" ;;
                3) LINE3_COMPONENTS="duration lines_changed" ;;
            esac
        else
            # 解析用户输入
            local parsed=$(parse_components "$input")
            case $line_num in
                1) LINE1_COMPONENTS="$parsed" ;;
                2) LINE2_COMPONENTS="$parsed" ;;
                3) LINE3_COMPONENTS="$parsed" ;;
            esac
        fi

        # 检查是否为空
        local current_components=""
        case $line_num in
            1) current_components="$LINE1_COMPONENTS" ;;
            2) current_components="$LINE2_COMPONENTS" ;;
            3) current_components="$LINE3_COMPONENTS" ;;
        esac

        if [ -z "$current_components" ]; then
            echo -e "${YELLOW}⚠️ 警告：此行为空，将不显示任何内容${NC}"
            read -p "确认留空？[y/N]: " confirm
            [ "$confirm" = "y" ] || continue
        fi

        return
    done
}

prompt_token_options() {
    # 检查是否有任何行包含 tokens
    local has_tokens=false
    if echo "$LINE1_COMPONENTS $LINE2_COMPONENTS $LINE3_COMPONENTS" | grep -q "tokens"; then
        has_tokens=true
    fi

    if [ "$has_tokens" = false ]; then
        return
    fi

    print_header
    echo -e "${BOLD}🔢 Step $((LINE_COUNT + 2))/4: Token 显示选项${NC}"
    echo ""
    echo -e "${DIM}💡 选择要显示的 Token 指标：${NC}"
    echo ""

    read -p "显示输入量 (In)？[Y/n]: " choice
    case "$choice" in n|N) TOKEN_IN=false ;; esac

    read -p "显示输出量 (Out)？[Y/n]: " choice
    case "$choice" in n|N) TOKEN_OUT=false ;; esac

    read -p "显示总量 (Total)？[Y/n]: " choice
    case "$choice" in n|N) TOKEN_TOTAL=false ;; esac
}

show_summary() {
    print_header
    echo -e "${BOLD}════════ 📋 配置预览 ════════${NC}"
    echo ""

    echo -e "  ${CYAN}📏 行数:${NC} $LINE_COUNT 行"
    echo ""

    local line1_display=$(format_components_display "$LINE1_COMPONENTS")
    echo -e "  ${CYAN}1️⃣ 第一行:${NC}${line1_display:- (空)}"

    if [ $LINE_COUNT -ge 2 ]; then
        local line2_display=$(format_components_display "$LINE2_COMPONENTS")
        echo -e "  ${CYAN}2️⃣ 第二行:${NC}${line2_display:- (空)}"
    fi

    if [ $LINE_COUNT -ge 3 ]; then
        local line3_display=$(format_components_display "$LINE3_COMPONENTS")
        echo -e "  ${CYAN}3️⃣ 第三行:${NC}${line3_display:- (空)}"
    fi

    # Check if tokens in any line
    if echo "$LINE1_COMPONENTS $LINE2_COMPONENTS $LINE3_COMPONENTS" | grep -q "tokens"; then
        echo ""
        echo -e "  ${CYAN}Token 显示:${NC} In=$([ "$TOKEN_IN" = true ] && echo "✓" || echo "✗") Out=$([ "$TOKEN_OUT" = true ] && echo "✓" || echo "✗") Total=$([ "$TOKEN_TOTAL" = true ] && echo "✓" || echo "✗")"
    fi

    echo ""
    echo -e "${BOLD}══════════════════════════${NC}"
    echo ""
}

prompt_options() {
    # Step 1: 选择行数
    prompt_line_count

    # Step 2-4: 配置每行组件
    prompt_line_components 1
    if [ $LINE_COUNT -ge 2 ]; then
        prompt_line_components 2
    fi
    if [ $LINE_COUNT -ge 3 ]; then
        prompt_line_components 3
    fi

    # Step 5: Token 选项
    prompt_token_options

    # 显示预览并确认
    while true; do
        show_summary
        echo -e "${DIM}🎮 操作: (c)✅确认安装 (e)🔄重新配置 (q)🚪退出${NC}"
        echo ""
        read -p "请选择 [c/e/q]: " choice

        case "$choice" in
            c|C|"")
                return
                ;;
            e|E)
                prompt_line_count
                prompt_line_components 1
                if [ $LINE_COUNT -ge 2 ]; then
                    prompt_line_components 2
                fi
                if [ $LINE_COUNT -ge 3 ]; then
                    prompt_line_components 3
                fi
                prompt_token_options
                ;;
            q|Q)
                echo "🚪 已取消安装"
                exit 0
                ;;
        esac
    done
}

generate_config() {
    print_info "⚙️ 生成配置文件..."

    PY_TOKEN_IN=$([ "$TOKEN_IN" = true ] && echo "True" || echo "False")
    PY_TOKEN_OUT=$([ "$TOKEN_OUT" = true ] && echo "True" || echo "False")
    PY_TOKEN_TOTAL=$([ "$TOKEN_TOTAL" = true ] && echo "True" || echo "False")

    $PYTHON_CMD << PYTHON_EOF
import json
import os

config_path = os.path.expanduser("~/.claude/statusline-config.json")

# Parse component lists
line1_str = """$LINE1_COMPONENTS"""
line2_str = """$LINE2_COMPONENTS"""
line3_str = """$LINE3_COMPONENTS"""

line1_components = line1_str.split() if line1_str.strip() else []
line2_components = line2_str.split() if line2_str.strip() else []
line3_components = line3_str.split() if line3_str.strip() else []

# Build token format
token_parts = []
if ${PY_TOKEN_IN}:
    token_parts.append("In:{input}")
if ${PY_TOKEN_OUT}:
    token_parts.append("Out:{output}")
if ${PY_TOKEN_TOTAL}:
    token_parts.append("Total:{total}")
token_format = " | ".join(token_parts) if token_parts else "In:{input} | Out:{output} | Total:{total}"

# Build lines configuration
lines = []
if line1_components:
    lines.append({"components": line1_components, "separator": " | "})
if line2_components:
    lines.append({"components": line2_components, "separator": " | "})
if line3_components:
    lines.append({"components": line3_components, "separator": " | "})

if not lines:
    lines = [{"components": ["model", "progress_bar"], "separator": " | "}]

config = {
    "lines": lines,
    "progress_bar": {
        "width": 10,
        "filled_char": "█",
        "empty_char": "░",
        "show_percentage": True
    },
    "colors": {
        "enabled": True,
        "low": {"threshold": 50, "color": "green"},
        "medium": {"threshold": 75, "color": "yellow"},
        "high": {"threshold": 90, "color": "red"}
    },
    "tokens": {
        "format": token_format,
        "unit": "k"
    },
    "components": {
        "model": {"format": "{name}"},
        "version": {"format": "v{version}"},
        "directory": {"max_length": 20, "show_git_root": True},
        "git": {"show_branch": True, "show_changes": True},
        "cost": {"format": "\${cost}"},
        "duration": {"format": "{duration}"},
        "tokens_cached": {"format": "cached:{cached}", "unit": "k"},
        "lines_changed": {"format": "+{added} -{removed}"},
        "context_usable": {"format": "{percent:.1f}%"},
        "custom_text": {"text": ""},
        "weekly_usage": {"format": "Weekly: {percent:.1f}%"},
        "block_timer": {"format": "Block: {elapsed}"}
    }
}

with open(config_path, "w", encoding="utf-8") as f:
    json.dump(config, f, indent=2, ensure_ascii=False)

print(f"配置文件已保存")
PYTHON_EOF
}

install() {
    print_info "🚀 开始安装 Claude Code Statusline..."
    check_python

    # 如果没有设置默认值，进行交互式配置
    if [ -z "$LINE1_COMPONENTS" ]; then
        prompt_options
    fi

    # Create .claude directory
    if [ ! -d "$CLAUDE_DIR" ]; then
        mkdir -p "$CLAUDE_DIR"
        print_info "📁 创建目录 $CLAUDE_DIR"
    fi

    # Copy statusline script
    if [ -f "$STATUSLINE_SCRIPT" ]; then
        print_warning "发现已存在的 statusline.py，创建备份..."
        cp "$STATUSLINE_SCRIPT" "$STATUSLINE_SCRIPT.backup"
    fi

    cp "$SCRIPT_DIR/statusline.py" "$STATUSLINE_SCRIPT"
    chmod +x "$STATUSLINE_SCRIPT"
    print_success "已安装 statusline.py 📄"

    # Generate config
    generate_config
    print_success "⚙️ 配置文件已生成"

    # Update settings.json
    update_settings

    echo ""
    print_success "🎉 安装完成！"
    echo ""
    echo -e "${DIM}🧪 测试命令:${NC}"
    echo "  echo '{\"model\":{\"display_name\":\"Opus\"},\"context_window\":{\"used_percentage\":45}}' | $PYTHON_CMD $STATUSLINE_SCRIPT"
    echo ""
    echo -e "${DIM}📄 配置文件:${NC} $CONFIG_FILE"
    echo -e "${DIM}🔄 重启 Claude Code 即可看到新的状态栏！${NC}"
}

update_settings() {
    print_info "⚙️ 更新 Claude Code 设置..."

    if [ ! -f "$SETTINGS_FILE" ]; then
        echo '{}' > "$SETTINGS_FILE"
    fi

    if grep -q '"statusLine"' "$SETTINGS_FILE" 2>/dev/null; then
        print_warning "settings.json 中已存在 statusLine 配置"
        if [ "$OPT_QUICK" = false ]; then
            read -p "是否覆盖？(y/N) " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                print_info "⏭️ 跳过 settings.json 更新"
                return
            fi
        fi
    fi

    cp "$SETTINGS_FILE" "$SETTINGS_FILE.backup"

    $PYTHON_CMD << 'EOF'
import json
import os

settings_path = os.path.expanduser("~/.claude/settings.json")

try:
    with open(settings_path, "r") as f:
        settings = json.load(f)
except (json.JSONDecodeError, FileNotFoundError):
    settings = {}

settings["statusLine"] = {
    "type": "command",
    "command": f"python3 {os.path.expanduser('~/.claude/statusline.py')}"
}

with open(settings_path, "w") as f:
    json.dump(settings, f, indent=2)

print("已更新 settings.json")
EOF

    print_success "✅ 已更新 $SETTINGS_FILE"
}

uninstall() {
    print_info "🗑️ 卸载 Claude Code Statusline..."

    if [ -f "$STATUSLINE_SCRIPT" ]; then
        rm "$STATUSLINE_SCRIPT"
        print_success "已删除 statusline.py"
    fi

    if [ -f "$CONFIG_FILE" ]; then
        read -p "是否保留配置文件？(Y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Nn]$ ]]; then
            cp "$CONFIG_FILE" "$CONFIG_FILE.backup"
            print_info "📦 配置已备份"
        fi
        rm "$CONFIG_FILE"
        print_success "已删除配置文件"
    fi

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
        print("已移除 statusLine 配置")
except:
    pass
EOF
        print_success "已清理 settings.json"
    fi

    echo ""
    print_success "👋 卸载完成！"
}

reconfigure() {
    print_info "🔄 重新配置状态栏..."
    check_python
    prompt_options
    generate_config
    print_success "✨ 配置已更新！重启 Claude Code 以应用"
}

show_help() {
    echo "🚀 Claude Code Statusline 安装器"
    echo ""
    echo -e "${BOLD}📖 用法:${NC} $0 [选项]"
    echo ""
    echo -e "${BOLD}⚙️ 选项:${NC}"
    echo "  无参数          🎯 交互式安装（推荐）"
    echo "  --quick, -q     ⚡ 快速安装（使用默认配置）"
    echo "  --reconfigure   🔄 重新配置"
    echo "  --uninstall     🗑️ 卸载"
    echo "  --help, -h      ❓ 显示帮助"
    echo ""
    echo -e "${BOLD}💡 示例:${NC}"
    echo "  $0              # 交互式安装"
    echo "  $0 --quick      # 快速安装"
    echo "  $0 --reconfigure # 重新配置"
}

# Quick install defaults
set_defaults() {
    LINE_COUNT=2
    LINE1_COMPONENTS="model directory git"
    LINE2_COMPONENTS="progress_bar tokens cost duration"
    TOKEN_IN=true
    TOKEN_OUT=true
    TOKEN_TOTAL=true
    OPT_QUICK=true
}

# Parse arguments
case "${1:-}" in
    --uninstall|-u)
        check_python
        uninstall
        exit 0
        ;;
    --reconfigure|-r)
        reconfigure
        exit 0
        ;;
    --quick|-q)
        set_defaults
        check_python
        ;;
    --help|-h)
        show_help
        exit 0
        ;;
    --install|-i|"")
        ;;
    *)
        print_error "❌ 未知选项: $1"
        show_help
        exit 1
        ;;
esac

# Run install
install
