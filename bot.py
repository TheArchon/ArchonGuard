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

import asyncio,logging
from pyrogram import Client
from config import settings
from database import Database
from services.cache import Cache
from handlers import start,admin,moderation,support

logging.basicConfig(level=getattr(logging,settings.log_level.upper(),logging.INFO),
                    format="%(asctime)s | %(levelname)s | %(message)s")

async def main():
    if not settings.api_id or not settings.api_hash or not settings.bot_token:
        raise RuntimeError("Set API_ID, API_HASH and BOT_TOKEN in .env")
    db=Database(settings.db_path); await db.init()
    cache=Cache(settings.redis_url); await cache.connect()
    app=Client("archonguard",api_id=settings.api_id,api_hash=settings.api_hash,
               bot_token=settings.bot_token,workers=32,sleep_threshold=30,
               max_concurrent_transmissions=8)
    start.register(app,db); admin.register(app,db,settings); moderation.register(app,db,settings); support.register(app,db,settings)
    async with app:
        asyncio.create_task(moderation.expiry_loop(app,db,settings.scheduler_interval))
        me=await app.get_me(); logging.info("Started @%s",me.username or me.id)
        await asyncio.Event().wait()
    await cache.close()

if __name__=="__main__": asyncio.run(main())
