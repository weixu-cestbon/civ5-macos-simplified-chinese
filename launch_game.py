#!/usr/bin/env python3
"""Launch the Steam macOS edition of Civilization V with a scoped environment."""

import argparse
from datetime import datetime
import os
from pathlib import Path
import plistlib
import subprocess
import sys
import tempfile


BUNDLE_ID = "com.aspyr.civ5xp.steam"
DEFAULT_APP = (
    Path.home()
    / "Library/Application Support/Steam/steamapps/common"
    / "Sid Meier's Civilization V/Civilization V.app"
)
DEFAULT_LOGS = Path.home() / "Library/Logs/Civ5LaunchHelper"


def validate_app(app):
    """Restrict the helper to the Steam macOS bundle; never modify it."""
    app = Path(app).expanduser().resolve()
    info = app / "Contents/Info.plist"
    try:
        with info.open("rb") as stream:
            metadata = plistlib.load(stream)
    except (OSError, plistlib.InvalidFileException, ValueError) as exc:
        raise ValueError("找不到有效的游戏应用，请用 --game 指定 Civilization V.app。") from exc
    if metadata.get("CFBundleIdentifier") != BUNDLE_ID:
        raise ValueError("仅支持 Steam macOS 版 Civilization V，不支持 App Store 版。")
    executable = app / "Contents/MacOS/Civilization V"
    if not executable.is_file() or not os.access(executable, os.X_OK):
        raise ValueError("游戏执行文件缺失或不可执行，请先通过 Steam 验证游戏文件。")
    return executable


def launch_environment(source):
    """Change only the child environment, preserving the caller's environment."""
    result = dict(source)
    result.pop("DYLD_INSERT_LIBRARIES", None)
    result["SteamAppId"] = "8930"
    result["SteamGameId"] = "8930"
    return result


def game_is_running():
    # Match either the native launcher or the game, not arbitrary command lines.
    result = subprocess.run(
        ["/usr/bin/pgrep", "-f", r"Civilization V\.app/Contents/MacOS/(AppBundleExe|Civilization V)( |$)"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode not in (0, 1):
        raise RuntimeError("无法确认游戏是否已退出，请关闭游戏后再试。")
    return result.returncode == 0


def create_log(directory):
    directory = Path(directory).expanduser()
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    prefix = "launch-" + datetime.now().strftime("%Y%m%d-%H%M%S") + "-"
    # mkstemp creates a unique owner-only file, even in an existing directory.
    fd, name = tempfile.mkstemp(prefix=prefix, suffix=".log", dir=directory)
    return Path(name), os.fdopen(fd, "w", encoding="utf-8")


def run_game(executable, environment, log):
    """Run the existing official binary with the same working directory as the tested script."""
    with subprocess.Popen(
        [str(executable)],
        cwd=executable.parent,
        env=environment,
        stdout=log,
        stderr=subprocess.STDOUT,
    ) as process:
        try:
            returncode = process.wait()
        except KeyboardInterrupt:
            # A foreground terminal interrupt reaches the game as well. Wait for
            # normal shutdown rather than reporting success or killing it.
            print("等待游戏退出；也可以在游戏菜单中选择退出。")
            while True:
                try:
                    returncode = process.wait()
                    break
                except KeyboardInterrupt:
                    continue
    log.write("\nExit code: {}\n".format(returncode))
    log.flush()
    return returncode


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game", type=Path, default=DEFAULT_APP, help="Civilization V.app 路径")
    parser.add_argument("--logs-dir", type=Path, default=DEFAULT_LOGS, help="本地日志目录")
    parser.add_argument("--dry-run", action="store_true", help="检查路径，不启动游戏或写入日志")
    args = parser.parse_args(argv)
    if sys.platform != "darwin":
        parser.exit(2, "仅支持 macOS。\n")
    try:
        executable = validate_app(args.game)
        if args.dry_run:
            print("路径检查通过：{}".format(executable))
            print("将直接启动游戏，仅在子进程中移除 DYLD_INSERT_LIBRARIES。")
            return 0
        if game_is_running():
            raise RuntimeError("文明 V 或启动器已在运行，请先正常退出，避免重复启动。")
        environment = launch_environment(os.environ)
        path, log = create_log(args.logs_dir)
        print("请保持 Steam 已启动并登录。")
        print("正在启动文明 V；本地运行日志：{}".format(path), flush=True)
        with log:
            returncode = run_game(executable, environment, log)
        if returncode == 0:
            print("游戏进程已正常退出。是否成功进入对局，请以游戏内实际表现为准。")
        else:
            print("游戏进程异常退出（{}）。日志保存在本机。".format(returncode), file=sys.stderr)
        return returncode if returncode >= 0 else min(255, 128 - returncode)
    except (OSError, ValueError, RuntimeError) as exc:
        parser.exit(1, "启动失败：{}\n".format(exc))


if __name__ == "__main__":
    raise SystemExit(main())
