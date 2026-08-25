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

import asyncio,time,io,os
from datetime import datetime,timezone
from pyrogram import filters
from pyrogram.types import ChatPermissions
from PIL import Image, ImageDraw, ImageFont
from utils import is_admin,contains_link
from services.flood import FloodGuard
from services.nsfw import NSFWDetector
from i18n import tr, normalize

PROBATION=dict(can_send_messages=True,can_send_media_messages=False,can_send_other_messages=False,can_add_web_page_previews=False,can_send_polls=False)
FULL=dict(can_send_messages=True,can_send_media_messages=True,can_send_other_messages=True,can_add_web_page_previews=True,can_send_polls=True)

async def make_welcome_card(client, chat, user, lang="en"):
    """Generate a localized welcome card without failing the join handler."""
    W,H=1200,630
    img=Image.new("RGB",(W,H),(16,18,24)); d=ImageDraw.Draw(img)
    # subtle premium background
    for x in range(0,W,80): d.line((x,0,x,H),fill=(24,27,36),width=1)
    for y in range(0,H,80): d.line((0,y,W,y),fill=(24,27,36),width=1)
    try:
        font_big=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",72)
        font_mid=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",42)
        font_small=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",30)
    except Exception:
        font_big=font_mid=font_small=ImageFont.load_default()
    # avatar
    avatar=None
    try:
        if user.photo:
            raw=await client.download_media(user, in_memory=True)
            if raw:
                avatar=Image.open(raw).convert("RGB").resize((250,250))
    except Exception:
        avatar=None
    if avatar is None:
        avatar=Image.new("RGB",(250,250),(55,61,78))
        ad=ImageDraw.Draw(avatar)
        initials=(user.first_name or user.username or "U")[:1].upper()
        box=ad.textbbox((0,0),initials,font=font_big); ad.text(((250-(box[2]-box[0]))/2,(250-(box[3]-box[1]))/2-8),initials,font=font_big,fill="white")
    mask=Image.new("L",(250,250),0); md=ImageDraw.Draw(mask); md.ellipse((0,0,250,250),fill=255)
    img.paste(avatar,(95,175),mask)
    name=user.first_name or "New Member"
    if len(name)>24: name=name[:21]+"..."
    group=chat.title or "this group"
    if len(group)>30: group=group[:27]+"..."
    d.text((400,120),tr(lang,"welcome"),font=font_big,fill="white")
    d.text((400,225),name,font=font_mid,fill=(126,180,255))
    d.text((400,300),f"to {group}",font=font_small,fill=(220,224,232))
    welcome_line = tr(lang, "welcome_message", name=name).split("\n")[0]
    d.text((400,385),welcome_line[:42],font=font_small,fill=(170,176,190))
    d.rounded_rectangle((400,475,760,535),radius=18,outline=(75,82,100),width=2)
    d.text((425,488),"Protected by ArchonGuard",font=font_small,fill=(145,151,166))
    out=io.BytesIO(); out.name="welcome.png"; img.save(out,"PNG"); out.seek(0)
    return out

def register(app,db,settings):
    flood=FloodGuard(settings.flood_limit,settings.flood_window)
    detector=NSFWDetector(settings.nsfw_api_url,settings.nsfw_api_key,settings.nsfw_threshold)

    async def punish(c,m,reason,mute=False,ban=False,score=None):
        lang=await db.get_language(m.from_user.id,"en")
        try: await m.delete()
        except Exception: pass
        action="delete"
        try:
            if ban:
                await c.ban_chat_member(m.chat.id,m.from_user.id); action="delete+ban"
            elif mute:
                await c.restrict_chat_member(m.chat.id,m.from_user.id,permissions=ChatPermissions(can_send_messages=False)); action="delete+mute"
        except Exception: pass
        await db.log(m.chat.id,m.from_user.id,action,reason,score)
        g=await db.group(m.chat.id)
        if g.get("log_chat_id"):
            try: await c.send_message(g["log_chat_id"],tr(lang,"log",action=action,user=m.from_user.id,reason=reason))
            except Exception: pass

    @app.on_message(filters.new_chat_members)
    async def joined(c,m):
        g=await db.group(m.chat.id)
        if not g["enabled"]: return
        # Welcome and probation are independent settings.
        # /welcome off disables only the welcome message; /newmember off
        # disables only the probation system.
        until=int(datetime.now(timezone.utc).timestamp())+g["duration"]
        for u in m.new_chat_members:
            if u.is_bot: continue

            if g.get("welcome"):
                try:
                    user_lang = await db.get_language(
                        u.id, normalize(getattr(u, "language_code", "en") or "en")
                    )
                    welcome_text = tr(user_lang, "welcome_message", name=u.first_name or "New Member")
                    card=await make_welcome_card(c,m.chat,u,user_lang)
                    await c.send_photo(m.chat.id, card, caption=welcome_text)
                except Exception:
                    pass

            if not g["new_member"]:
                continue
            if await db.is_whitelisted(m.chat.id,u.id) or await is_admin(c,m.chat.id,u.id): continue
            try:
                await c.restrict_chat_member(m.chat.id,u.id,permissions=ChatPermissions(**PROBATION))
                await db.set_restriction(m.chat.id,u.id,until)
            except Exception: pass

    @app.on_message(filters.group & ~filters.service)
    async def moderate(c,m):
        if not m.from_user or m.from_user.is_bot:return
        g=await db.group(m.chat.id)
        if not g["enabled"] or await db.is_whitelisted(m.chat.id,m.from_user.id) or await is_admin(c,m.chat.id,m.from_user.id):return
        if g["lockdown"]: await punish(c,m,"lockdown"); return
        until=await db.restriction(m.chat.id,m.from_user.id)
        if until and until>int(time.time()) and m.media:
            await punish(c,m,"probation-media"); return
        text=(m.text or m.caption or "").lower()
        if g["antilink"] and contains_link(text): await punish(c,m,"link"); return
        words=await db.badwords(m.chat.id)
        if any(w in text for w in words):
            n=await db.add_warning(m.chat.id,m.from_user.id)
            await punish(c,m,"badword",mute=n>=settings.warn_mute_at,ban=n>=settings.repeat_offender_ban_at); return
        if g["antiflood"] and flood.hit((m.chat.id,m.from_user.id)):
            n=await db.add_warning(m.chat.id,m.from_user.id)
            await punish(c,m,"flood",mute=True,ban=n>=settings.repeat_offender_ban_at); return
        if g["nsfw"] and m.media:
            flagged,score,source=await detector.check(c,m)
            if flagged: await punish(c,m,"nsfw:"+source,mute=True,score=score)

async def expiry_loop(app,db,interval):
    while True:
        try:
            for c,u in await db.expired(int(time.time())):
                try: await app.restrict_chat_member(c,u,permissions=ChatPermissions(**FULL))
                except Exception: pass
                await db.clear_restriction(c,u)
        except Exception: pass
        await asyncio.sleep(interval)
