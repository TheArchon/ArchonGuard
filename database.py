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

import os, aiosqlite, time

class Database:
    def __init__(self,path): self.path=path

    async def init(self):
        os.makedirs(os.path.dirname(self.path) or ".",exist_ok=True)
        async with aiosqlite.connect(self.path) as db:
            await db.executescript("""
            PRAGMA journal_mode=WAL;
            PRAGMA synchronous=NORMAL;
            PRAGMA busy_timeout=5000;
            CREATE TABLE IF NOT EXISTS groups(
              chat_id INTEGER PRIMARY KEY, enabled INTEGER DEFAULT 1,
              new_member INTEGER DEFAULT 1, duration INTEGER DEFAULT 86400,
              antilink INTEGER DEFAULT 0, antiflood INTEGER DEFAULT 0,
              nsfw INTEGER DEFAULT 0, lockdown INTEGER DEFAULT 0,
              welcome INTEGER DEFAULT 1, log_chat_id INTEGER);
            CREATE TABLE IF NOT EXISTS restrictions(
              chat_id INTEGER,user_id INTEGER,until_ts INTEGER,
              PRIMARY KEY(chat_id,user_id));
            CREATE INDEX IF NOT EXISTS idx_restrictions_until ON restrictions(until_ts);
            CREATE TABLE IF NOT EXISTS whitelist(chat_id INTEGER,user_id INTEGER,PRIMARY KEY(chat_id,user_id));
            CREATE TABLE IF NOT EXISTS warnings(chat_id INTEGER,user_id INTEGER,count INTEGER DEFAULT 0,PRIMARY KEY(chat_id,user_id));
            CREATE TABLE IF NOT EXISTS badwords(chat_id INTEGER,word TEXT,PRIMARY KEY(chat_id,word));
            CREATE TABLE IF NOT EXISTS user_languages(user_id INTEGER PRIMARY KEY,lang TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS moderation_log(
              id INTEGER PRIMARY KEY AUTOINCREMENT,chat_id INTEGER,user_id INTEGER,
              action TEXT,reason TEXT,score REAL,created_ts INTEGER);
            CREATE TABLE IF NOT EXISTS bug_reports(
              id INTEGER PRIMARY KEY AUTOINCREMENT,chat_id INTEGER,user_id INTEGER,
              created_ts INTEGER NOT NULL);
            CREATE INDEX IF NOT EXISTS idx_bug_reports_user_chat ON bug_reports(chat_id,user_id,created_ts);
            """)
            try:
                await db.execute("ALTER TABLE groups ADD COLUMN welcome INTEGER DEFAULT 1")
            except Exception:
                pass
            await db.commit()

    async def ensure(self,c):
        async with aiosqlite.connect(self.path) as db:
            await db.execute("INSERT OR IGNORE INTO groups(chat_id,duration) VALUES(?,?)",(c,86400))
            await db.commit()

    async def group(self,c):
        await self.ensure(c)
        async with aiosqlite.connect(self.path) as db:
            db.row_factory=aiosqlite.Row
            r=await (await db.execute("SELECT * FROM groups WHERE chat_id=?",(c,))).fetchone()
            return dict(r)

    async def set_group(self,c,key,value):
        allowed={"enabled","new_member","duration","antilink","antiflood","nsfw","lockdown","welcome","log_chat_id"}
        if key not in allowed: raise ValueError("invalid setting")
        await self.ensure(c)
        async with aiosqlite.connect(self.path) as db:
            await db.execute(f"UPDATE groups SET {key}=? WHERE chat_id=?",(value,c)); await db.commit()

    async def set_restriction(self,c,u,until):
        async with aiosqlite.connect(self.path) as db:
            await db.execute("""INSERT INTO restrictions VALUES(?,?,?)
            ON CONFLICT(chat_id,user_id) DO UPDATE SET until_ts=excluded.until_ts""",(c,u,until)); await db.commit()

    async def restriction(self,c,u):
        async with aiosqlite.connect(self.path) as db:
            r=await (await db.execute("SELECT until_ts FROM restrictions WHERE chat_id=? AND user_id=?",(c,u))).fetchone()
            return r[0] if r else None

    async def expired(self,now):
        async with aiosqlite.connect(self.path) as db:
            return await (await db.execute("SELECT chat_id,user_id FROM restrictions WHERE until_ts<=?",(now,))).fetchall()

    async def clear_restriction(self,c,u):
        async with aiosqlite.connect(self.path) as db:
            await db.execute("DELETE FROM restrictions WHERE chat_id=? AND user_id=?",(c,u)); await db.commit()

    async def whitelist(self,c,u,enabled=True):
        async with aiosqlite.connect(self.path) as db:
            if enabled: await db.execute("INSERT OR IGNORE INTO whitelist VALUES(?,?)",(c,u))
            else: await db.execute("DELETE FROM whitelist WHERE chat_id=? AND user_id=?",(c,u))
            await db.commit()

    async def is_whitelisted(self,c,u):
        async with aiosqlite.connect(self.path) as db:
            return bool(await (await db.execute("SELECT 1 FROM whitelist WHERE chat_id=? AND user_id=?",(c,u))).fetchone())

    async def add_warning(self,c,u):
        async with aiosqlite.connect(self.path) as db:
            await db.execute("INSERT OR IGNORE INTO warnings VALUES(?,?,0)",(c,u))
            await db.execute("UPDATE warnings SET count=count+1 WHERE chat_id=? AND user_id=?",(c,u)); await db.commit()
            return (await (await db.execute("SELECT count FROM warnings WHERE chat_id=? AND user_id=?",(c,u))).fetchone())[0]

    async def warnings(self,c,u):
        async with aiosqlite.connect(self.path) as db:
            r=await (await db.execute("SELECT count FROM warnings WHERE chat_id=? AND user_id=?",(c,u))).fetchone()
            return r[0] if r else 0

    async def clear_warnings(self,c,u):
        async with aiosqlite.connect(self.path) as db:
            await db.execute("DELETE FROM warnings WHERE chat_id=? AND user_id=?",(c,u)); await db.commit()

    async def badword(self,c,w,add=True):
        async with aiosqlite.connect(self.path) as db:
            if add: await db.execute("INSERT OR IGNORE INTO badwords VALUES(?,?)",(c,w.lower()))
            else: await db.execute("DELETE FROM badwords WHERE chat_id=? AND word=?",(c,w.lower()))
            await db.commit()

    async def badwords(self,c):
        async with aiosqlite.connect(self.path) as db:
            return [r[0] for r in await (await db.execute("SELECT word FROM badwords WHERE chat_id=?",(c,))).fetchall()]

    async def set_language(self,u,lang):
        async with aiosqlite.connect(self.path) as db:
            await db.execute("""INSERT INTO user_languages VALUES(?,?)
            ON CONFLICT(user_id) DO UPDATE SET lang=excluded.lang""",(u,lang)); await db.commit()

    async def get_language(self,u,default="en"):
        async with aiosqlite.connect(self.path) as db:
            r=await (await db.execute("SELECT lang FROM user_languages WHERE user_id=?",(u,))).fetchone()
            return r[0] if r else default

    async def log(self,c,u,a,r,score=None):
        async with aiosqlite.connect(self.path) as db:
            await db.execute("INSERT INTO moderation_log(chat_id,user_id,action,reason,score,created_ts) VALUES(?,?,?,?,?,?)",
                             (c,u,a,r,score,int(time.time()))); await db.commit()

    async def bug_recent(self,c,u,seconds=300):
        cutoff=int(time.time())-seconds
        async with aiosqlite.connect(self.path) as db:
            r=await (await db.execute(
                "SELECT created_ts FROM bug_reports WHERE chat_id=? AND user_id=? ORDER BY created_ts DESC LIMIT 1",
                (c,u))).fetchone()
            return bool(r and r[0] >= cutoff)

    async def add_bug_report(self,c,u):
        async with aiosqlite.connect(self.path) as db:
            await db.execute("INSERT INTO bug_reports(chat_id,user_id,created_ts) VALUES(?,?,?)",
                             (c,u,int(time.time())))
            await db.commit()
