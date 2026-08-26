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

from pyrogram import filters
from i18n import tr, normalize
from html import escape


def _message_link(chat, message_id):
    if not message_id:
        return None
    username = getattr(chat, "username", None)
    if username:
        return f"https://t.me/{username}/{message_id}"
    chat_id = getattr(chat, "id", 0)
    if str(chat_id).startswith("-100"):
        return f"https://t.me/c/{str(chat_id)[4:]}/{message_id}"
    return None


async def _group_link(client, chat):
    username = getattr(chat, "username", None)
    if username:
        return f"https://t.me/{username}"
    invite = getattr(chat, "invite_link", None)
    if invite:
        return invite
    try:
        invite = await client.export_chat_invite_link(chat.id)
        if invite:
            return invite
    except Exception:
        pass
    return None


def _user_label(user):
    name = " ".join(x for x in [getattr(user, "first_name", None), getattr(user, "last_name", None)] if x)
    username = getattr(user, "username", None)
    if username:
        return f"{name or username} (@{username})"
    return name or str(user.id)


def register(app, db, settings):
    @app.on_message(filters.command("bug") & filters.group, group=-1)
    async def bug_report(client, message):
        if not message.from_user:
            return

        lang = await db.get_language(
            message.from_user.id,
            normalize(getattr(message.from_user, "language_code", "en") or "en"),
        )
        g = await db.group(message.chat.id)
        logger_chat_id = g.get("log_chat_id") or getattr(settings, "logger_chat_id", 0)

        if not logger_chat_id:
            await message.reply_text(tr(lang, "bug_unavailable"))
            return

        if await db.bug_recent(message.chat.id, message.from_user.id, 300):
            await message.reply_text(tr(lang, "bug_cooldown"))
            return

        # /bug <description> OR reply to a problematic message with /bug.
        description = " ".join(message.command[1:]).strip() if len(message.command) > 1 else ""
        reported = message.reply_to_message
        if not description and not reported:
            await message.reply_text(tr(lang, "bug_missing"))
            return

        group_link = await _group_link(client, message.chat)
        report_link = _message_link(message.chat, message.id)
        reported_link = _message_link(message.chat, reported.id) if reported else None
        reporter = escape(_user_label(message.from_user))
        title = escape(message.chat.title or "Unknown group")

        lines = [
            "🐞 <b>GUARDIAN BUG REPORT</b>",
            "",
            f"👤 <b>Reporter:</b> {reporter}",
            f"🆔 <b>User ID:</b> <code>{message.from_user.id}</code>",
            f"👥 <b>Group:</b> {title}",
            f"🆔 <b>Group ID:</b> <code>{message.chat.id}</code>",
        ]
        if group_link:
            lines.append(f"🔗 <b>Group:</b> <a href=\"{group_link}\">Open group</a>")
        if description:
            safe = escape(description)
            lines.append(f"📝 <b>Report:</b> {safe}")
        if reported:
            reported_text = (reported.text or reported.caption or "[media/service message]").strip()
            if len(reported_text) > 700:
                reported_text = reported_text[:697] + "..."
            lines.append(f"💬 <b>Reported message:</b> {escape(reported_text)}")
            if reported_link:
                lines.append(f"📎 <b>Message link:</b> <a href=\"{reported_link}\">Open message</a>")
        if report_link:
            lines.append(f"📨 <b>Report command:</b> <a href=\"{report_link}\">Open report</a>")

        try:
            await client.send_message(logger_chat_id, "\n".join(lines), disable_web_page_preview=True)
            await db.add_bug_report(message.chat.id, message.from_user.id)
            await message.reply_text(tr(lang, "bug_sent"))
        except Exception:
            await message.reply_text(tr(lang, "bug_failed"))
