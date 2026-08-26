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
from pyrogram.types import ChatPermissions
from utils import is_admin,target_user,parse_duration
from i18n import tr

async def allowed(c,m): return bool(m.from_user and await is_admin(c,m.chat.id,m.from_user.id))

def register(app,db,settings):
    @app.on_message(filters.command(["status","config"]) & filters.group)
    async def status(c,m):
        if not await allowed(c,m): return
        g=await db.group(m.chat.id); lang=await db.get_language(m.from_user.id,"en")
        duration = g["duration"]
        if duration % 3600 == 0:
            duration_text = f"{duration // 3600}h"
        elif duration % 60 == 0:
            duration_text = f"{duration // 60}m"
        else:
            duration_text = f"{duration}s"
        await m.reply_text(
            f"🛡️ ArchonGuard\n"
            f"New-member: {tr(lang,'on') if g['new_member'] else tr(lang,'off')}\n"
            f"Duration: {duration_text}\n"
            f"Anti-link: {tr(lang,'on') if g['antilink'] else tr(lang,'off')}\n"
            f"Anti-flood: {tr(lang,'on') if g['antiflood'] else tr(lang,'off')}\n"
            f"NSFW: {tr(lang,'on') if g['nsfw'] else tr(lang,'off')}\n"
            f"Welcome: {tr(lang,'on') if g.get('welcome') else tr(lang,'off')}\n"
            f"Lockdown: {tr(lang,'on') if g['lockdown'] else tr(lang,'off')}")
    @app.on_message(filters.command(["newmember","antilink","antiflood","nsfw","lockdown","welcome"]) & filters.group)
    async def toggle(c,m):
        if not await allowed(c,m) or len(m.command)<2:
            return

        lang=await db.get_language(m.from_user.id,"en")
        setting_map = {
            "newmember": "new_member",
            "antilink": "antilink",
            "antiflood": "antiflood",
            "nsfw": "nsfw",
            "lockdown": "lockdown",
            "welcome": "welcome",
        }

        command = m.command[0].lower()
        setting = setting_map.get(command)
        if not setting:
            return

        enabled = int(m.command[1].lower() in ("on","1","true","yes"))

        if setting == "lockdown":
            try:
                if enabled:
                    # Lock normal members at Telegram permission level.
                    # Chat administrators/owner remain allowed by Telegram.
                    await c.set_chat_permissions(
                        m.chat.id,
                        ChatPermissions(
                            can_send_messages=False,
                            can_send_media_messages=False,
                            can_send_other_messages=False,
                            can_add_web_page_previews=False,
                            can_send_polls=False
                        )
                    )
                else:
                    # Restore normal member permissions.
                    await c.set_chat_permissions(
                        m.chat.id,
                        ChatPermissions(
                            can_send_messages=True,
                            can_send_media_messages=True,
                            can_send_other_messages=True,
                            can_add_web_page_previews=True,
                            can_send_polls=True
                        )
                    )

                await db.set_group(m.chat.id,"lockdown",enabled)
                await m.reply_text(tr(lang,"updated"))

            except Exception as e:
                await m.reply_text(
                    f"Lockdown error: {type(e).__name__}: {e}"
                )
            return

        await db.set_group(m.chat.id,setting,enabled)
        await m.reply_text(tr(lang,"updated"))

    @app.on_message(filters.command("duration") & filters.group)
    async def duration(c,m):
        if not await allowed(c,m) or len(m.command)<2:return
        v=parse_duration(m.command[1]); lang=await db.get_language(m.from_user.id,"en")
        if not v or not 60<=v<=604800:
            return await m.reply_text(tr(lang,"duration_invalid"))

        await db.set_group(m.chat.id,"duration",v)

        if v < 3600:
            minutes = v // 60
            await m.reply_text(f"Duration set: {minutes} minute(s)")
        else:
            hours = v // 3600
            await m.reply_text(f"Duration set: {hours} hour(s)")
    @app.on_message(filters.command(["whitelist","unwhitelist"]) & filters.group)
    async def white(c,m):
        if await allowed(c,m):
            u=target_user(m); lang=await db.get_language(m.from_user.id,"en")
            if u: await db.whitelist(m.chat.id,u,m.command[0]=="whitelist"); await m.reply_text(tr(lang,"updated"))
    @app.on_message(filters.command(["warn","unwarn","warnings"]) & filters.group)
    async def warn(c,m):
        if not await allowed(c,m):return
        u=target_user(m); lang=await db.get_language(m.from_user.id,"en")
        if not u:return
        if m.command[0]=="warn":
            n=await db.add_warning(m.chat.id,u); await m.reply_text(tr(lang,"warning_count",count=n))
            if n>=settings.warn_mute_at:
                try: await c.restrict_chat_member(m.chat.id,u,permissions=ChatPermissions(can_send_messages=False))
                except Exception: pass
        elif m.command[0]=="unwarn":
            await db.clear_warnings(m.chat.id,u); await m.reply_text(tr(lang,"warning_reset"))
        else: await m.reply_text(tr(lang,"warning_count",count=await db.warnings(m.chat.id,u)))
    @app.on_message(filters.command(["setbadword","delbadword"]) & filters.group)
    async def bw(c,m):
        if await allowed(c,m) and len(m.command)>1:
            await db.badword(m.chat.id,m.command[1],m.command[0]=="setbadword"); lang=await db.get_language(m.from_user.id,"en"); await m.reply_text(tr(lang,"updated"))
    @app.on_message(filters.command("badwords") & filters.group)
    async def bws(c,m):
        if await allowed(c,m): await m.reply_text(", ".join(await db.badwords(m.chat.id)) or "none")
    @app.on_message(filters.command("setlogchat") & filters.group)
    async def log(c,m):
        if await allowed(c,m):
            lang=await db.get_language(m.from_user.id,"en")
            target = m.command[1] if len(m.command) > 1 else str(m.chat.id)
            try:
                target_id = int(target)
            except ValueError:
                return await m.reply_text(tr(lang,"log_chat_invalid"))
            await db.set_group(m.chat.id,"log_chat_id",target_id)
            await m.reply_text(tr(lang,"updated"))
