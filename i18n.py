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

import json, os
from pathlib import Path

LOCALE_DIR = Path(__file__).parent / "locales"
LANGUAGES = {}
TRANSLATIONS = {}

for path in LOCALE_DIR.glob("*.json"):
    data=json.loads(path.read_text(encoding="utf-8"))
    meta=data.pop("_meta")
    LANGUAGES[meta["code"]]=meta
    TRANSLATIONS[meta["code"]]=data

def normalize(code):
    code=(code or "en").lower().replace("-","_")
    aliases={"zh":"zh_cn","zh_cn":"zh_cn","zh_tw":"zh_tw","in":"id","iw":"he","he_il":"he","pt_br":"pt"}
    return aliases.get(code, code if code in TRANSLATIONS else "en")

def tr(lang,key,**kwargs):
    lang=normalize(lang)
    text=TRANSLATIONS.get(lang,TRANSLATIONS["en"]).get(key,TRANSLATIONS["en"].get(key,key))
    try: return text.format(**kwargs)
    except Exception: return text

def language_buttons():
    return list(LANGUAGES.values())
