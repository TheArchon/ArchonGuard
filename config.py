# ============================================================
# ArchonGuard
# Copyright (c) 2026 TeamArchon
#
# Developed by: TeamArchon
# Project: ArchonGuard — Telegram Group Security Bot
#
# This source code is part of the ArchonGuard project.
# Please retain this credit when modifying or redistributing
# the source code.
# ============================================================

import os
from dataclasses import dataclass
from dotenv import load_dotenv
load_dotenv()

@dataclass(frozen=True)
class Settings:
    api_id: int = int(os.getenv("API_ID", "0"))
    api_hash: str = os.getenv("API_HASH", "")
    bot_token: str = os.getenv("BOT_TOKEN", "")
    owner_id: int = int(os.getenv("OWNER_ID", "0"))
    owner_username: str = os.getenv("OWNER_USERNAME", "")
    logger_chat_id: int = int(os.getenv("LOGGER_CHAT_ID", "0"))
    bot_username: str = os.getenv("BOT_USERNAME", "")
    db_path: str = os.getenv("DB_PATH", "data/archonguard.db")
    redis_url: str = os.getenv("REDIS_URL", "")
    nsfw_api_url: str = os.getenv("NSFW_API_URL", "")
    nsfw_api_key: str = os.getenv("NSFW_API_KEY", "")
    nsfw_threshold: float = float(os.getenv("NSFW_THRESHOLD", "0.85"))
    default_duration: int = int(os.getenv("DEFAULT_DURATION", "86400"))
    flood_limit: int = int(os.getenv("FLOOD_LIMIT", "8"))
    flood_window: int = int(os.getenv("FLOOD_WINDOW", "8"))
    warn_mute_at: int = int(os.getenv("WARN_MUTE_AT", "3"))
    repeat_offender_ban_at: int = int(os.getenv("REPEAT_OFFENDER_BAN_AT", "5"))
    scheduler_interval: int = int(os.getenv("SCHEDULER_INTERVAL", "15"))
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    source_github: str = os.getenv("SOURCE_GITHUB", "")
    source_channel: str = os.getenv("SOURCE_CHANNEL", "")
    support_url: str = os.getenv("SUPPORT_URL", "")
    updates_url: str = os.getenv("UPDATES_URL", "")
settings = Settings()
