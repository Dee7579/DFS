"""Launch a DFS APK on an Android emulator and require a live ready marker."""

from __future__ import annotations

import argparse
from pathlib import Path
import re
import subprocess
import time


def _run(
    command: list[str],
    *,
    check: bool = False,
    text: bool = True,
) -> subprocess.CompletedProcess:
    return subprocess.run(
        command,
        check=check,
        capture_output=True,
        text=text,
    )


def _badging_identity(output: str) -> tuple[str, str]:
    package_match = re.search(r"^package: name='([^']+)'", output, re.MULTILINE)
    activity_match = re.search(
        r"^launchable-activity: name='([^']+)'",
        output,
        re.MULTILINE,
    )
    if not package_match or not activity_match:
        raise RuntimeError("aapt could not identify the APK package and launch activity.")
    return package_match.group(1), activity_match.group(1)


def _capture_diagnostics(adb: str, package: str, directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    commands = {
        "logcat.txt": [adb, "logcat", "-d", "-v", "threadtime"],
        "activity.txt": [
            adb,
            "shell",
            "dumpsys",
            "activity",
            "activities",
        ],
        "package.txt": [adb, "shell", "dumpsys", "package", package],
    }
    for filename, command in commands.items():
        result = _run(command)
        (directory / filename).write_text(
            (result.stdout or "") + (result.stderr or ""),
            encoding="utf-8",
        )
    screenshot = _run([adb, "exec-out", "screencap", "-p"], text=False)
    if screenshot.returncode == 0:
        (directory / "screen.png").write_bytes(screenshot.stdout)


def verify_startup(
    *,
    adb: str,
    aapt: str,
    apk: Path,
    diagnostics: Path,
    timeout: float,
) -> None:
    badging = _run([aapt, "dump", "badging", str(apk)], check=True).stdout
    package, activity = _badging_identity(badging)
    component = f"{package}/{activity}"

    try:
        _run([adb, "install", "-r", str(apk)], check=True)
        _run([adb, "shell", "am", "force-stop", package])
        _run(
            [
                adb,
                "shell",
                "run-as",
                package,
                "rm",
                "-f",
                "files/dfs-startup-status.txt",
            ]
        )
        _run([adb, "logcat", "-c"], check=True)
        launch = _run([adb, "shell", "am", "start", "-W", "-n", component])
        print(launch.stdout, end="")
        if launch.returncode:
            raise RuntimeError(launch.stderr or f"Android could not launch {component}.")

        deadline = time.monotonic() + timeout
        last_status = ""
        while time.monotonic() < deadline:
            status = _run(
                [
                    adb,
                    "shell",
                    "run-as",
                    package,
                    "cat",
                    "files/dfs-startup-status.txt",
                ]
            )
            if status.returncode == 0 and status.stdout.strip():
                last_status = status.stdout.strip()
                first_line = last_status.splitlines()[0]
                if first_line == "error":
                    raise RuntimeError(f"DFS reported a startup error:\n{last_status}")
                if first_line == "ready":
                    time.sleep(3)
                    process = _run([adb, "shell", "pidof", package])
                    if process.returncode or not process.stdout.strip():
                        raise RuntimeError(
                            "DFS reached ready state but its Android process then exited."
                        )
                    print(f"DFS emulator startup passed for {package} ({last_status}).")
                    return
            time.sleep(1)
        suffix = f" Last marker: {last_status}" if last_status else ""
        raise RuntimeError(f"DFS did not reach ready state within {timeout:.0f}s.{suffix}")
    finally:
        _capture_diagnostics(adb, package, diagnostics)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--adb", default="adb")
    parser.add_argument("--aapt", required=True)
    parser.add_argument("--apk", type=Path, required=True)
    parser.add_argument("--diagnostics", type=Path, required=True)
    parser.add_argument("--timeout", type=float, default=45)
    args = parser.parse_args()
    verify_startup(
        adb=args.adb,
        aapt=args.aapt,
        apk=args.apk.resolve(),
        diagnostics=args.diagnostics.resolve(),
        timeout=args.timeout,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
