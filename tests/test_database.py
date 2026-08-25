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

import pytest
from database import Database

@pytest.mark.asyncio
async def test_db(tmp_path):
    db=Database(str(tmp_path/"test.db")); await db.init()
    g=await db.group(-100)
    assert g["new_member"]==1
    await db.set_restriction(-100,5,9999999999)
    assert await db.restriction(-100,5)==9999999999
    await db.whitelist(-100,5)
    assert await db.is_whitelisted(-100,5)
    await db.set_language(5,"hi")
    assert await db.get_language(5)=="hi"
