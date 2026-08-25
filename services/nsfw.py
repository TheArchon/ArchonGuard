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

import httpx
class NSFWDetector:
    def __init__(self,url,key,threshold):
        self.url,self.key,self.threshold=url,key,threshold
    async def check(self,client,message):
        if not self.url:return False,0.0,"disabled"
        if not (message.photo or message.video or message.animation or message.document):
            return False,0.0,"no-media"
        try:
            f=await client.download_media(message,in_memory=True)
            if not f:return False,0.0,"download-failed"
            headers={"Authorization":f"Bearer {self.key}"} if self.key else {}
            async with httpx.AsyncClient(timeout=25) as x:
                r=await x.post(self.url,headers=headers,files={"file":("media.bin",f.getvalue())})
                r.raise_for_status(); data=r.json()
            score=float(data.get("score",0))
            return bool(data.get("flagged",False)) or score>=self.threshold,score,"provider"
        except Exception:
            return False,0.0,"provider-error"
