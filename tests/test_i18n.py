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

from i18n import LANGUAGES,TRANSLATIONS,tr
def test_all_languages_loaded():
    assert len(LANGUAGES)==33
    required={"start_title","add","source","support","help","owner","language","back","protection","members","nsfw","flood","link","settings","stats","commands","warnings","lockdown","help_text","help_commands"}
    for code in LANGUAGES:
        assert required.issubset(TRANSLATIONS[code])
def test_format():
    assert tr("en","warning_count",count=3)=="Warnings: 3"
