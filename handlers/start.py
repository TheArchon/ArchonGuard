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
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import settings
from i18n import tr, LANGUAGES, normalize
import emoji

def main_menu(lang):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"{emoji.ADD} {tr(lang,'add')}",url=f"https://t.me/{settings.bot_username}?startgroup=true")],
        [InlineKeyboardButton(f"{emoji.SOURCE} {tr(lang,'source')}",callback_data="ag:source"),
         InlineKeyboardButton(f"{emoji.SUPPORT} {tr(lang,'support')}",callback_data="ag:support")],
        [InlineKeyboardButton(f"{emoji.HELP} {tr(lang,'help')}",callback_data="ag:help"),
         InlineKeyboardButton(f"{emoji.OWNER} {tr(lang,'owner')}",url=f"https://t.me/{settings.owner_username.lstrip('@')}")],
        [InlineKeyboardButton(f"{emoji.LANGUAGE} {tr(lang,'language')}",callback_data="ag:language")]
    ])

def start_text(lang):
    return f"{emoji.SHIELD} **{tr(lang,'start_title')}**\n\n{emoji.SECURITY} **{tr(lang,'start_sub')}**\n\n{tr(lang,'start_desc')}"

def help_menu(lang):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"{emoji.SHIELD} {tr(lang,'protection')}",callback_data="ag:help:protection"),
         InlineKeyboardButton(f"{emoji.MEMBER} {tr(lang,'members')}",callback_data="ag:help:members")],
        [InlineKeyboardButton(f"{emoji.NSFW} {tr(lang,'nsfw')}",callback_data="ag:help:nsfw"),
         InlineKeyboardButton(f"{emoji.FLOOD} {tr(lang,'flood')}",callback_data="ag:help:flood")],
        [InlineKeyboardButton(f"{emoji.LINK} {tr(lang,'link')}",callback_data="ag:help:link"),
         InlineKeyboardButton(f"{emoji.WARNING} {tr(lang,'warnings')}",callback_data="ag:help:warnings")],
        [InlineKeyboardButton(f"{emoji.LOCK} {tr(lang,'lockdown')}",callback_data="ag:help:lockdown"),
         InlineKeyboardButton(f"{emoji.COMMANDS} {tr(lang,'commands')}",callback_data="ag:help:commands")],
        [InlineKeyboardButton(f"{emoji.BACK} {tr(lang,'back')}",callback_data="ag:back")]
    ])

def language_menu():
    rows=[]; items=list(LANGUAGES.values())
    for i in range(0,len(items),2):
        row=[InlineKeyboardButton(f"{items[i]['flag']} {items[i]['name']}",callback_data=f"ag:lang:{items[i]['code']}")]
        if i+1<len(items):
            row.append(InlineKeyboardButton(f"{items[i+1]['flag']} {items[i+1]['name']}",callback_data=f"ag:lang:{items[i+1]['code']}"))
        rows.append(row)
    rows.append([InlineKeyboardButton(f"{emoji.BACK} Back",callback_data="ag:back")])
    return InlineKeyboardMarkup(rows)

def register(app,db):
    @app.on_message(filters.command("start"))
    async def start(_,m):
        lang=await db.get_language(m.from_user.id,normalize(getattr(m.from_user,"language_code","en")))
        await m.reply_text(start_text(lang),reply_markup=main_menu(lang))

    @app.on_callback_query(filters.regex(r"^ag:"))
    async def callbacks(client,q):
        user=q.from_user
        lang=await db.get_language(user.id,normalize(getattr(user,"language_code","en")))
        data=q.data
        if data=="ag:back":
            await q.answer()
            await q.message.edit_text(start_text(lang),reply_markup=main_menu(lang)); return
        if data=="ag:language":
            await q.answer(); await q.message.edit_text(f"🌐 **{tr(lang,'language_text')}**",reply_markup=language_menu()); return
        if data.startswith("ag:lang:"):
            new=normalize(data.split(":")[-1]); await db.set_language(user.id,new)
            await q.answer(tr(new,"saved",lang=LANGUAGES[new]["name"]))
            await q.message.edit_text(start_text(new),reply_markup=main_menu(new)); return
        if data=="ag:source":
            kb=InlineKeyboardMarkup([
                [InlineKeyboardButton(f"{emoji.GITHUB} GitHub",url=settings.source_github or "https://github.com"),
                 InlineKeyboardButton(f"{emoji.CHANNEL} Channel",url=settings.source_channel or "https://t.me")],
                [InlineKeyboardButton(f"{emoji.BACK} {tr(lang,'back')}",callback_data="ag:back")]])
            await q.answer(); await q.message.edit_text(f"📡 **{tr(lang,'source')}**\n\n{tr(lang,'source_text')}",reply_markup=kb); return
        if data=="ag:support":
            kb=InlineKeyboardMarkup([
                [InlineKeyboardButton(f"{emoji.SUPPORT} {tr(lang,'support')}",url=settings.support_url or "https://t.me"),
                 InlineKeyboardButton(f"{emoji.CHANNEL} {'Updates'}",url=settings.updates_url or "https://t.me")],
                [InlineKeyboardButton(f"{emoji.BACK} {tr(lang,'back')}",callback_data="ag:back")]])
            await q.answer(); await q.message.edit_text(f"💬 **{tr(lang,'support')}**\n\n{tr(lang,'support_text')}",reply_markup=kb); return
        if data=="ag:help":
            await q.answer(); await q.message.edit_text(f"📖 **{tr(lang,'help')}**\n\n{tr(lang,'help_text')}",reply_markup=help_menu(lang)); return
        if data.startswith("ag:help:"):
            key=data.split(":")[-1]
            await q.answer()
            text_key={"protection":"help_protection","members":"help_members","nsfw":"help_nsfw","flood":"help_flood","link":"help_link","warnings":"help_warnings","lockdown":"help_lockdown","commands":"help_commands"}.get(key,"help_text")
            await q.message.edit_text(f"📖 **{tr(lang,key if key in ('protection','members','nsfw','flood','link','warnings','lockdown','commands') else 'help')}**\n\n{tr(lang,text_key)}",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(f"{emoji.BACK} {tr(lang,'back')}",callback_data="ag:help")]]))
