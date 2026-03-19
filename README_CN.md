# Claude Code 状态栏

一个可定制的 Claude Code CLI 状态栏，用于显示上下文使用情况、Git 状态、模型信息等。

## 功能特性

- 🎨 **完全可定制** - 自由配置显示内容和样式
- 📊 **上下文进度条** - 可视化显示上下文窗口使用率，带颜色编码
- 🔀 **Git 集成** - 显示分支名称和变更数量
- 🤖 **模型信息** - 显示当前使用的 Claude 模型
- 💰 **成本追踪** - 显示会话成本
- ⏱️ **时长显示** - 显示会话持续时间
- 🎯 **多行支持** - 可将信息分布在多行显示

## 安装

### 交互式安装（推荐）

```bash
git clone https://github.com/yourusername/claude-code-statusline.git
cd claude-code-statusline
./install.sh
```

安装程序会提示你配置以下选项：
- **布局模式**：单行或双行显示
- **Git 信息**：显示分支名和修改状态
- **Token 统计**：显示输入/输出/总 token 数
- **会话费用**：显示当前会话花费
- **会话时长**：显示会话持续时间

### 快速安装

使用默认配置（单行模式，包含 Git、Token、费用）：

```bash
./install.sh --quick
```

### 重新配置

修改配置而无需重新安装：

```bash
./install.sh --reconfigure
```

### 手动安装

1. 将 `statusline.py` 复制到 `~/.claude/`
2. 将 `config.json` 复制到 `~/.claude/statusline-config.json`
3. 在 `~/.claude/settings.json` 中添加以下配置：

```json
{
  "statusLine": {
    "type": "command",
    "command": "python3 ~/.claude/statusline.py"
  }
}
```

4. 重启 Claude Code

## 卸载

```bash
./install.sh --uninstall
```

## 可用命令

| 命令 | 说明 |
|------|------|
| `./install.sh` | 交互式安装 |
| `./install.sh --quick` | 快速安装（默认配置） |
| `./install.sh --reconfigure` | 重新配置选项 |
| `./install.sh --uninstall` | 卸载状态栏 |

## 配置说明

配置文件位于 `~/.claude/statusline-config.json`。

### 基本结构

```json
{
  "lines": [
    {
      "components": ["model", "directory", "git"],
      "separator": " | "
    }
  ],
  "progress_bar": {
    "width": 10,
    "filled_char": "█",
    "empty_char": "░",
    "gradient_char": "▓"
  },
  "colors": {
    "enabled": true,
    "low": {"threshold": 50, "color": "green"},
    "medium": {"threshold": 75, "color": "yellow"},
    "high": {"threshold": 90, "color": "red"}
  }
}
```

### 可用组件

| 组件 | 描述 | 示例输出 |
|------|------|----------|
| `progress_bar` | 上下文使用进度条 | `████████░░` |
| `model` | 当前 Claude 模型 | `Opus 4.6` |
| `directory` | 当前工作目录 | `~/projects/myapp` |
| `git` | Git 分支和变更 | `main [+2 ~3]` |
| `tokens` | Token 统计 | `in:12.5k out:3.2k total:15.7k` |
| `cost` | 会话成本 | `$0.0234` |
| `duration` | 会话时长 | `5m30s` |

### 进度条配置

```json
{
  "progress_bar": {
    "width": 10,
    "filled_char": "█",
    "empty_char": "░",
    "gradient_char": "▓"
  }
}
```

- `width`: 进度条字符数
- `filled_char`: 已填充部分的字符
- `empty_char`: 未填充部分的字符
- `gradient_char`: 边界处的渐变字符

### 颜色配置

```json
{
  "colors": {
    "enabled": true,
    "low": {"threshold": 50, "color": "green"},
    "medium": {"threshold": 75, "color": "yellow"},
    "high": {"threshold": 90, "color": "red"}
  }
}
```

- 颜色根据上下文窗口使用百分比自动变化
- 可用颜色：`green`、`yellow`、`orange`、`red`、`blue`、`cyan`、`magenta`

### Token 格式配置

```json
{
  "tokens": {
    "format": "in:{input} out:{output} total:{total}",
    "unit": "k"
  }
}
```

- `format`: 带占位符的模板字符串
- `unit`: `k` 表示千，`m` 表示百万，`auto` 自动选择

### 组件特定选项

```json
{
  "components": {
    "model": {
      "format": "{name}"
    },
    "directory": {
      "max_length": 20,
      "show_git_root": true
    },
    "git": {
      "show_branch": true,
      "show_changes": true
    },
    "cost": {
      "format": "${cost}"
    },
    "duration": {
      "format": "{duration}"
    }
  }
}
```

## 配置示例

### 最小配置

只显示必要信息 - 进度条和模型名称：

```json
{
  "lines": [
    {
      "components": ["progress_bar", "model"],
      "separator": " "
    }
  ]
}
```

### 完整配置

启用所有功能，带 emoji 图标：

```json
{
  "lines": [
    {
      "components": ["model", "directory", "git"],
      "separator": " | "
    },
    {
      "components": ["progress_bar", "tokens", "cost", "duration"],
      "separator": " | "
    }
  ]
}
```

### 紧凑单行

所有信息显示在一行：

```json
{
  "lines": [
    {
      "components": ["progress_bar", "model", "directory", "tokens", "cost"],
      "separator": " | "
    }
  ]
}
```

## 测试

无需重启 Claude Code 即可测试配置：

```bash
echo '{"model":{"display_name":"Opus"},"context_window":{"used_percentage":45,"input_tokens":12500,"output_tokens":3200}}' | python3 ~/.claude/statusline.py
```

## 故障排除

### 状态栏不显示

1. 确认已安装 Python 3：`python3 --version`
2. 检查脚本是否有执行权限：`ls -la ~/.claude/statusline.py`
3. 验证 settings.json 配置是否正确

### 颜色不生效

确保终端支持 ANSI 颜色代码。尝试运行：
```bash
echo -e "\033[32m绿色\033[0m"
```

### Git 信息不显示

确保当前目录是 Git 仓库或其子目录。

## 项目结构

```
Claude-Code-Statusline/
├── README.md           # 英文文档
├── README_CN.md        # 中文文档
├── install.sh          # 安装脚本
├── statusline.py       # 主脚本
├── config.json         # 默认配置
└── examples/
    ├── minimal.json    # 最小配置
    ├── full.json       # 完整配置
    └── multiline.json  # 多行布局示例
```

## 贡献

欢迎提交 Pull Request！

## 许可证

MIT License
