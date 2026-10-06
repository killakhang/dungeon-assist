"""Invite/onboarding helpers for Wopples' Dungeon Buddy."""
import os
from urllib.parse import urlencode

def invite_url(client_id=None):
    client_id=client_id or os.getenv("DISCORD_CLIENT_ID","")
    if not client_id:
        return None
    # Minimal useful permissions: view/send/read history/embed/attach.
    permissions=274877975552
    q=urlencode({"client_id":client_id,"scope":"bot applications.commands","permissions":permissions})
    return "https://discord.com/oauth2/authorize?"+q

def vtt_url(guild_id, token):
    base=os.getenv("PUBLIC_VTT_URL","").rstrip("/")
    if not base: return None
    return base+"/?guild="+str(guild_id)+"&token="+token
