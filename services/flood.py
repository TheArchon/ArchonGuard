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

import time
from collections import defaultdict,deque
class FloodGuard:
    def __init__(self,limit,window):
        self.limit,self.window=limit,window; self.events=defaultdict(deque)
    def hit(self,key):
        now=time.monotonic(); q=self.events[key]
        while q and now-q[0]>self.window:q.popleft()
        q.append(now); return len(q)>self.limit
