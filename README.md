# ArchonGuard — Complete Production Build

## Included
- 24h default new-member probation; configurable 1m–7d
- Text allowed during probation; media/GIF/sticker/poll/web-preview restrictions
- Automatic expiry with SQLite persistence and restart recovery
- Admin + whitelist bypass
- Anti-link
- Anti-flood
- Bad-word warnings, automatic mute and repeat-offender ban
- Emergency lockdown
- Optional real NSFW classifier adapter
- Moderation logs
- Redis-ready cache layer
- Interactive /start UI
- Add Me / Source / Support / Help / Owner / Language buttons
- Source and Support callback panels with 2 top buttons + Back
- Help category callbacks
- 33-language extensible i18n system
- Automatic Telegram language fallback + manual language selector
- Docker deployment
- Unit tests

## Important
Telegram inline keyboard buttons accept text but do not support attaching arbitrary custom-emoji MessageEntity objects to button labels. The UI therefore uses Unicode emoji in buttons. Custom/premium emoji can be added to message text using Telegram custom-emoji entities if valid IDs are supplied.

NSFW is intentionally an adapter: set `NSFW_API_URL` and `NSFW_API_KEY` for a real classifier. The provider should accept multipart `file` and return JSON like:
{"flagged": true, "score": 0.97}
For videos/GIFs, the provider should perform frame sampling.

Before deployment, replace the public URLs and owner/bot usernames in `.env`.
Required Telegram admin permissions: Delete Messages + Restrict Members.


## Welcome System

New members can receive a premium generated welcome card with their profile photo, name, group name and ArchonGuard branding. Admins can use `/welcome on` or `/welcome off`. The feature is enabled by default.
