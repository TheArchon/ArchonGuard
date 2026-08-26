# ============================================================
# ArchonGuard
# Copyright (c) 2026 TeamArchon
#
# Developed by: TeamArchon
# Project: ArchonGuard — Telegram Group Security Bot
#
# Developed by: TeamArchon
# ============================================================

import asyncio
import os
import subprocess
import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
BACKUP_DIR = BASE_DIR / ".update_backup"


async def run_command(*args):
    proc = await asyncio.create_subprocess_exec(
        *args,
        cwd=str(BASE_DIR),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    stdout, _ = await proc.communicate()
    return proc.returncode, stdout.decode(errors="replace").strip()


async def update_bot():
    code, _ = await run_command(
        "git", "rev-parse", "--is-inside-work-tree"
    )
    if code != 0:
        return False, "❌ Git repository not found."

    code, status = await run_command(
        "git", "status", "--porcelain"
    )
    if code != 0:
        return False, "❌ Unable to check Git status."

    if status:
        return False, (
            "⚠️ Update cancelled.\n\n"
            "VPS has uncommitted/local changes.\n"
            "Please commit or stash them before using /update."
        )

    code, current_commit = await run_command(
        "git", "rev-parse", "HEAD"
    )
    if code != 0:
        return False, "❌ Could not determine current commit."

    BACKUP_DIR.mkdir(exist_ok=True)
    (BACKUP_DIR / "previous_commit").write_text(current_commit)

    code, output = await run_command(
        "git", "fetch", "origin", "main"
    )
    if code != 0:
        return False, f"❌ GitHub fetch failed.\n\n{output[-1500:]}"

    code, remote_commit = await run_command(
        "git", "rev-parse", "origin/main"
    )
    if code != 0:
        return False, "❌ Could not read GitHub main."

    if current_commit == remote_commit:
        return False, (
            "✅ Already up to date.\n\n"
            f"Commit: `{current_commit[:7]}`"
        )

    code, merge_base = await run_command(
        "git", "merge-base", current_commit, remote_commit
    )

    if code != 0 or merge_base != current_commit:
        return False, (
            "❌ Update cancelled.\n\n"
            "Local branch has diverged from GitHub main.\n"
            "Manual Git merge/recovery is required."
        )

    # Detect dependency changes before updating.
    code, changed_files = await run_command(
        "git", "diff", "--name-only",
        current_commit, remote_commit
    )

    requirements_changed = (
        code == 0
        and "requirements.txt" in changed_files.splitlines()
    )

    code, output = await run_command(
        "git", "merge", "--ff-only", "origin/main"
    )

    if code != 0:
        await run_command(
            "git", "reset", "--hard", current_commit
        )
        return False, (
            "❌ Update failed.\n\n"
            "Previous version restored."
        )

    code, compile_output = await run_command(
        sys.executable, "-m", "compileall", "-q", "."
    )

    if code != 0:
        await run_command(
            "git", "reset", "--hard", current_commit
        )
        return False, (
            "❌ Updated code failed syntax check.\n\n"
            "Previous version restored."
        )

    if requirements_changed:
        code, pip_output = await run_command(
            sys.executable,
            "-m",
            "pip",
            "install",
            "-r",
            "requirements.txt",
        )

        if code != 0:
            await run_command(
                "git", "reset", "--hard", current_commit
            )
            return False, (
                "❌ Dependency installation failed.\n\n"
                "Previous version restored."
            )

    return True, (
        "✅ Update successful.\n\n"
        f"Previous: `{current_commit[:7]}`\n"
        f"Updated: `{remote_commit[:7]}`\n\n"
        "🔄 Restarting bot..."
    )


async def restart_bot():
    await asyncio.sleep(2)

    subprocess.Popen(
        [sys.executable, "bot.py"],
        cwd=str(BASE_DIR),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )

    os._exit(0)
