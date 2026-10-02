# 文明 V macOS 简体中文补丁

这是一个非官方、开源的《文明 V》Steam macOS 版简体中文补丁构建与可回滚安装工具。

> 本仓库只发布原创工具代码，不分发游戏文本、Steam depot、Apple 字体或生成后的补丁。用户必须拥有游戏及相应 DLC，所有中文文本和字体图集均在用户自己的 Mac 上生成。

## 当前状态

- 已在 Steam Civ V 1.4.2、Apple Silicon、macOS 15.7.7 上验证。
- 支持本体、Gods & Kings 和 Brave New World。
- 保留英文语音，将界面及游戏文本转换为简体中文。
- 安装前自动备份，可以一键恢复。
- 目前仅支持 Steam macOS 版，不支持 Windows、Linux 和 Mac App Store 版。

## 中文从哪里来

本项目**没有自行翻译或抓取第三方汉化**，文本来自游戏所有者本人通过 Steam 下载的官方中文资源：

| 内容 | Steam depot | 原始语言 | 处理方式 |
| --- | ---: | --- | --- |
| 文明 V 本体 | `235586` | 官方中文资源 | 读取官方 `ZH_Hant_HK` 文本 |
| Gods & Kings | `16870` | 官方繁体中文 | OpenCC `t2s` 转简体 |
| Brave New World | `235580` | 官方繁体中文 | OpenCC `t2s` 转简体 |

构建器共读取约 140 个官方 XML、约 2 万条文本。它只转换 XML 的 `<Text>` 内容，不改动标签名、文本键值和游戏控制代码。Mac 版没有官方中文选项，因此补丁复用游戏已有的 `zh_Hant_HK` 数据库槽位，但显示内容是转换后的简体中文。

中文字体不是从仓库下载的。工具读取用户 Mac 上已经安装的中文字体，在本机生成 Civ V Mac 版需要的 DXT5 位图图集；生成物不会上传到 GitHub。

## 最简单的安装方法

### 准备条件

1. 使用 macOS，并通过 Steam 安装《文明 V》。
2. 在 Steam 中登录拥有该游戏及相应 DLC 的账号。
3. 完全退出《文明 V》，Steam 可以保持运行。
4. 安装 Python 3.11 或更高版本。可以在终端执行 `python3 --version` 检查。

### 一键安装

先获取工具代码，任选一种方式：

1. 在 GitHub 页面点击绿色 **Code** 按钮，选择 **Download ZIP**，下载后解压；或
2. 在终端执行：

```sh
git clone https://github.com/weixu-cestbon/civ5-macos-simplified-chinese.git
cd civ5-macos-simplified-chinese
```

随后在 Finder 中打开项目文件夹，双击：

```text
一键安装.command
```

也可以在终端运行：

```sh
./一键安装.command
```

脚本会依次完成：

1. 检查系统、Steam、游戏和 Python。
2. 检查三个官方中文 depot 是否已经下载。
3. 如果缺少 depot，自动打开 Steam 控制台，并把下载命令复制到剪贴板。
4. 创建项目专用 `.venv`，安装固定版本依赖。
5. 从本机 Steam 文件生成简体中文 XML 和 DXT5 字体。
6. 备份原游戏文件、配置和本地化缓存。
7. 安装补丁并提示启动游戏测试。

### 首次运行需要粘贴 Steam 命令

Steam 不允许第三方脚本绕过账号许可或 Steam Guard。如果脚本检测到 depot 缺失，它会打开 Steam 的 `CONSOLE` 页面，并将下面三条命令复制到剪贴板：

```text
download_depot 8930 235586
download_depot 8930 16870
download_depot 8930 235580
```

请在 Steam 控制台中**每次粘贴一行并按回车**，等待出现 `Depot download complete` 后再执行下一行。三项都完成后回到终端按回车，脚本会继续构建和安装。

默认下载位置是：

```text
~/Library/Application Support/Steam/Steam.AppBundle/Steam/Contents/MacOS/steamapps/content/app_8930/
```

如果 Steam 安装布局不同，可以在终端显式指定：

```sh
CIV5_STEAM_CONTENT="/你的路径/app_8930" ./一键安装.command
```

## 手动安装

不使用一键脚本时，可以逐步执行：

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python build_patch.py \
  --steam-root "$HOME/Library/Application Support/Steam/Steam.AppBundle/Steam/Contents/MacOS/steamapps/content/app_8930"
python install_patch.py
```

如需指定本机字体及 TTC 字体序号：

```sh
python build_patch.py --steam-root /path/to/app_8930 \
  --font /path/to/local/CJK-font.ttc --font-index 0
```

## 卸载与恢复

双击：

```text
一键恢复.command
```

或在项目环境中执行：

```sh
.venv/bin/python uninstall_patch.py
```

备份默认保存在：

```text
~/Library/Application Support/Sid Meier's Civilization 5/SimplifiedChineseBackup_时间/
```

Steam 更新或“验证游戏文件完整性”可能覆盖补丁，此后重新运行一键安装即可。卸载补丁不会删除游戏存档。

## 常见问题

### 双击脚本提示无法打开

先在终端进入项目目录，执行：

```sh
chmod +x 一键安装.command 一键恢复.command
./一键安装.command
```

如果 macOS 仍然阻止运行，再到“系统设置 → 隐私与安全性”中确认允许打开。不要关闭系统的整体安全保护。

### Steam 控制台没有出现

确保 Steam 已经启动并登录，然后在浏览器或终端打开：

```sh
open "steam://nav/console"
```

### 下载提示没有许可

确认当前 Steam 账号拥有《文明 V》及对应 DLC。脚本不会也不能绕过 Steam 所有权检查。

### 游戏更新后恢复英文

Steam 可能覆盖 `.app` 内的补丁文件。关闭游戏后重新运行 `一键安装.command`。

### 安装中文后启动时闪退

如果普通启动方式会退出，可以在 Steam 已启动并登录、游戏及原启动器均已正常退出后，在本项目目录尝试可选的启动入口：

```sh
python3 launch_game.py --dry-run
python3 launch_game.py
```

第一条命令只检查游戏路径；第二条直接运行原版游戏执行文件。安装在其他 Steam 库时，使用 `--game "/path/to/Civilization V.app"` 指定应用路径。本入口不会安装中文，也不会修改游戏资源、配置、缓存或存档；能正常启动的玩家无需使用。

它校验 Steam macOS 应用身份，将工作目录设为 `Contents/MacOS`，绕过 Aspyr 启动器，仅在游戏子进程中移除 `DYLD_INSERT_LIBRARIES` 并设置 Steam 应用编号。每次运行的输出保存在本机 `~/Library/Logs/Civ5LaunchHelper/` 的独立日志中，仅当前用户可读取；日志不会自动上传。该方式可能影响 Steam 叠加层或其他依赖注入的功能，多人联机尚未验证。

在一台 Apple Silicon Mac、macOS 26.5.1、Steam Civ V 1.4.2（180925）上，原始脚本采用此启动方式后，玩家确认英文和中文均可启动，并通过“快速开始”进入中文对局。此处整理的通用入口已通过自动化测试及本机路径检查，尚未再次进行实机启动回归。绕过启动器与移除注入变量同时发生，尚未逐项隔离根因；这不是所有闪退的通用修复，也不表示 Steam 原入口已恢复。

仍然失败时，可运行 `一键恢复.command` 恢复最近备份并比较原版表现，再提交 issue。请提供 Mac 型号、macOS 版本、Steam 游戏版本和报错现象；不要公开上传完整日志、崩溃报告、备份或含个人路径的截图。

## 合规与开源

本项目原创代码使用 MIT License。该许可证不适用于《文明 V》、官方文本、Steam depot、Apple 字体或用户本机生成物。生成后的 `dist/` 仅供配合用户本人合法游戏副本使用，请勿传播。

项目与 2K、Firaxis、Aspyr、Apple、Valve/Steam 均无隶属、赞助或背书关系。详见 [LEGAL.md](LEGAL.md) 和 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。

开发和发布检查：

```sh
python -m unittest discover -s tests
python scripts/release_audit.py
```
