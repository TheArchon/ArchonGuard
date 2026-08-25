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

from utils import contains_link,parse_duration
def test_link(): assert contains_link("https://example.com") and not contains_link("hello")
def test_duration(): assert parse_duration("24h")==86400 and parse_duration("30m")==1800
