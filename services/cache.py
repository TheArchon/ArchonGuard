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

class Cache:
    def __init__(self,url): self.url=url; self.client=None
    async def connect(self):
        if self.url:
            from redis.asyncio import Redis
            self.client=Redis.from_url(self.url,decode_responses=True)
    async def get(self,k): return await self.client.get(k) if self.client else None
    async def setex(self,k,s,v):
        if self.client: await self.client.setex(k,s,v)
    async def close(self):
        if self.client: await self.client.aclose()
