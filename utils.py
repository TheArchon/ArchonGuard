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

import re
from pyrogram.enums import ChatMemberStatus
URL_RE=re.compile(r"(https?://|www\.|t\.me/|telegram\.me/)",re.I)

def contains_link(text): return bool(URL_RE.search(text or ""))

def parse_duration(value):
    m=re.fullmatch(r"(\d+)\s*(s|m|h|d)?",value.strip().lower())
    if not m:return None
    return int(m.group(1))*{"s":1,"m":60,"h":3600,"d":86400}[m.group(2) or "s"]

async def is_admin(client,chat_id,user_id):
    try:
        return (await client.get_chat_member(chat_id,user_id)).status in (
            ChatMemberStatus.OWNER,ChatMemberStatus.ADMINISTRATOR)
    except Exception:return False

def target_user(message):
    if message.reply_to_message and message.reply_to_message.from_user:
        return message.reply_to_message.from_user.id
    if len(message.command)>1:
        try:return int(message.command[1])
        except ValueError:return None
    return None
