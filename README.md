# fishreader —— 终端摸鱼小说阅读器（CodeAgent 伪装版）

在终端里读小说的摸鱼工具。界面伪装成一个正在干活的代码 Agent：主体是持续滚动的英文日志，小说只占右侧一小块区域，伪装成工作笔记。老板走近时按一下老板键，界面立刻变成纯英文的工作台。

> ⚠️ 工具本身只做本地文件解析与展示，不含任何规避监控/公司策略的能力。请自行评估使用场景。

## 功能

- 自动扫描 `books/` 目录（可配置），支持 `.txt` / `.epub` / `.mobi`
- TXT 自动识别编码（UTF-8 / GBK / GB18030 / Big5），自动按章节拆分（`第一章`、`第3章`、`Chapter 1`、`CHAPTER IV` 等）
- EPUB 按 spine 顺序提取正文，自动清理脚本/样式/导航
- MOBI 优先用 `mobi` 库解包；失败时标记为不可读并说明原因（不阻塞其他书）
- 阅读进度自动保存（`.fish_progress.json`），重启续读
- 英文假日志持续滚动（planning / search / edit / test / git / review 六类模板随机组合），间隔可配置
- 老板键（默认 `b`）一键全屏英文模式，隐藏小说、关闭弹窗、过滤中文
- 阅读区伪装样式：`- 正文`（markdown 笔记）、`# 正文`（注释）、`"""` 文档字符串

## 安装

需要 **Python 3.11+**（建议 3.13）。

```bash
cd fish
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt      # 首次
.venv/bin/pip install -e .                     # 可选：安装 fishreader 命令
```

依赖：

| 包 | 用途 |
|---|---|
| `textual>=0.52,<9` | TUI 框架 |
| `beautifulsoup4>=4.12` | EPUB/MOBI HTML 清洗 |
| `charset-normalizer>=3.0` | TXT 编码识别 |
| `mobi>=0.4`（可选） | MOBI 解包，装不上时 .mobi 标为不可读，其余功能不受影响 |

## 使用

```bash
python run.py                 # 项目根目录执行
python run.py --config my.toml   # 指定配置文件
# 或安装后：fishreader
```

1. 把小说（`.txt` / `.epub` / `.mobi`）放进 `books/`（路径可在配置里改）。
2. 启动。首次启动会生成 `fish.toml` 并弹出书籍列表（伪装成 `Open recent files`）。
3. 回车打开，`→` 翻页，读到哪里关掉都行，下次启动自动回到上次位置。

### 按键

| 按键 | 功能 |
|---|---|
| `→` / `Space` / `PgDn` | 下一页 |
| `←` / `PgUp` | 上一页 |
| `↑` / `↓` | 上下滚动一行 |
| `n` / `p` | 下一章 / 上一章 |
| `t` | 打开章节目录（table of contents），`↑/↓` 选择后回车跳章 |
| `l` | 打开书籍列表（Open recent files） |
| `b` | 老板键：切换全屏英文伪装模式 |
| `q` | 退出并保存进度 |
| `Esc` | 关闭弹窗 |

### 老板键

- 按 `b`（可在配置里改成别的键）：阅读区立刻隐藏，日志占满全屏，所有界面文本为纯英文，若正开着弹窗也会一并关闭。
- 再按一次恢复原样，阅读位置不丢。
- 老板键是全局优先键，任何界面上都能触发。

## 配置（fish.toml）

首次启动自动生成带注释的默认配置。常用项：

```toml
[books]
scan_dirs = ["books"]            # 扫描目录（可多个，支持绝对路径）
extensions = [".epub", ".mobi", ".txt"]
allow_kindleunpack = false       # MOBI 失败时是否尝试外部 kindleunpack CLI

[reader]                         # 以下键修改后重启生效
font_size = "medium"             # small | medium | large（显示密度，不动终端真实字号）
line_spacing = 0                 # 逻辑行后额外空行；非 0 时覆盖 font_size 映射
paragraph_spacing = 0            # 段落后额外空行；非 0 时覆盖 font_size 映射
reader_width = "30%"             # 阅读区宽度："25%"~"40%" 或固定列数（如 36）
reader_position = "right"        # right | bottom（本版本使用 right）
novel_style = "markdown"         # markdown | comment | docstring
resume_last = true               # 启动续读上次书籍

[disguise]
agent_name = "CodeAgent"
agent_version = "0.4.2"
log_interval_min = 0.8           # 假日志最小/最大间隔（秒）
log_interval_max = 1.5
boss_key = "b"                   # 老板键
full_hide_chinese = true         # 老板模式过滤 CJK

[theme]
log_level_color = true           # 日志级别着色
reader_color = "gray"            # 阅读区颜色
accent = "green"

[progress]
file = ".fish_progress.json"
autosave_on_page = true          # 翻页即存进度；false 则仅退出时保存
```

说明：

- **font_size 是显示密度档位**，不改终端真实字号——真实字号请用终端自己的缩放快捷键。`small` 更紧凑（每页更多行），`large` 行距加大（每页更少行）。
- 阅读进度存在项目根的 `.fish_progress.json`，删除即重置。

## 常见问题

**MOBI 打不开？**
检查 `pip install mobi` 是否成功；失败文件会在书籍列表/打开时提示原因（多为 DRM）。可先在配置开启 `allow_kindleunpack` 并安装 `kindleunpack`，或转成 TXT/EPUB。

**提示 terminal too small？**
窗口至少需要 40 列 × 12 行；放大终端后重启。窗口过窄（<60 列）时阅读区会自动隐藏。

**书里的编码乱码？**
TXT 编码按 charset-normalizer 识别，兜底顺序 UTF-8 → GB18030 → GBK → Big5；个别文件仍可能识别失败，可自行转成 UTF-8。

**想换个字体/字号？**
见上：`font_size` 是应用内密度档位，真实字号用终端缩放（macOS Terminal/iTerm2：`Cmd`+`+` / `Cmd`+`-`）。

## 开发

```bash
.venv/bin/python -m unittest discover -s tests -v   # 单元测试
```

模块结构见 [docs/开发文档.md](docs/开发文档.md)。核心模块（解析、分页、配置、编码、假日志生成）都不依赖 TUI，可独立测试。

## 兼容性与隐私

- 优先支持 macOS / Linux 现代终端（Terminal、iTerm2、GNOME Terminal、kitty 等）；Windows Terminal 其次。
- 应用完全本地运行：不联网、不上传、不读取项目目录以外的文件（除非配置里显式指定路径）。