#!/usr/bin/env python3
"""
Fetches TF2 server data from the Steam API and posts/updates
a Discord message via webhook with a formatted server list.
"""

import json
import sys
import urllib.parse
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
MESSAGE_ID_FILE = SCRIPT_DIR / ".message_id"
WEBHOOK_URL_FILE = SCRIPT_DIR / ".webhook_url"
BASE_URL_FILE = SCRIPT_DIR / ".base_url"
STEAM_API_KEY_FILE = Path.home() / ".steam_api_key"

STEAM_API_URL = "https://api.steampowered.com/IGameServersService/GetServerList/v1/"
GAMETYPE_FILTER = "gleesus"


def load_file(path: Path, label: str) -> str:
    try:
        return path.read_text().strip()
    except FileNotFoundError:
        print(f"Error: {label} not found at {path}", file=sys.stderr)
        sys.exit(1)


def fetch_servers(api_key: str) -> list[dict]:
    params = urllib.parse.urlencode({
        "filter": r"\appid\440\region\7",
        "limit": "999",
        "key": api_key,
    })
    url = f"{STEAM_API_URL}?{params}"
    with urllib.request.urlopen(url, timeout=15) as resp:
        data = json.loads(resp.read())

    servers = data.get("response", {}).get("servers", [])
    return [
        s for s in servers
        if GAMETYPE_FILTER in s.get("gametype", "").lower()
    ]


def load_base_url() -> str | None:
    try:
        return BASE_URL_FILE.read_text().strip().rstrip("/")
    except FileNotFoundError:
        return None


def escape_discord(text: str) -> str:
    """Prevent Discord markdown interpretation (e.g. >>> becoming a blockquote)."""
    if text.startswith(">"):
        return "\u200b" + text
    return text


def build_server_field(s: dict, base_url: str | None) -> dict:
    addr = s.get("addr", "")
    name = escape_discord(s.get("name", "Unknown"))
    map_name = s.get("map", "?")
    players = s.get("players", 0)
    max_players = s.get("max_players", 0)
    bots = s.get("bots", 0)

    player_str = f"{players}/{max_players}"
    if bots:
        player_str += f" (+{bots} bots)"

    if base_url:
        connect = f"[Connect]({base_url}/connect.html?addr={addr})"
    else:
        connect = f"`connect {addr}`"

    return {
        "name": name,
        "value": f"`{map_name}` · **{player_str}** players · {connect}",
        "inline": False,
    }


def build_payload(servers: list[dict], base_url: str | None = None) -> dict:
    now = datetime.now(timezone.utc).isoformat()

    if not servers:
        return {
            "embeds": [{
                "title": "Community Servers",
                "description": "No servers currently online.",
                "color": 0x95a5a6,
                "timestamp": now,
            }]
        }

    servers.sort(key=lambda s: s.get("players", 0), reverse=True)

    active = [s for s in servers if s.get("players", 0) > 0]
    empty = [s for s in servers if s.get("players", 0) == 0]

    embeds = []

    if active:
        embeds.append({
            "title": "Active Servers",
            "color": 0xCF7C00,
            "fields": [build_server_field(s, base_url) for s in active],
        })

    if empty:
        embed = {
            "color": 0x546e7a,
            "fields": [build_server_field(s, base_url) for s in empty],
            "timestamp": now,
            "footer": {"text": "Auto-updated"},
        }
        if not active:
            embed["title"] = "Servers"
        else:
            embed["description"] = "-# Empty servers"
        embeds.append(embed)

    if active:
        embeds[-1]["timestamp"] = now
        embeds[-1]["footer"] = {"text": "Auto-updated"}

    return {"embeds": embeds}


def discord_request(url: str, payload: dict, method: str = "POST") -> dict:
    data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    req.add_header("User-Agent", "TF2CommunityWebhook/1.0")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"Discord API error {e.code}: {body}", file=sys.stderr)
        sys.exit(1)


def main():
    api_key = load_file(STEAM_API_KEY_FILE, "Steam API key")
    webhook_url = load_file(WEBHOOK_URL_FILE, "Discord webhook URL")
    message_id = (
        MESSAGE_ID_FILE.read_text().strip() if MESSAGE_ID_FILE.exists() else None
    )

    base_url = load_base_url()
    servers = fetch_servers(api_key)
    payload = build_payload(servers, base_url)

    if message_id:
        url = f"{webhook_url}/messages/{message_id}"
        discord_request(url, payload, method="PATCH")
        print(f"Updated message {message_id} ({len(servers)} servers)")
    else:
        url = f"{webhook_url}?wait=true"
        result = discord_request(url, payload)
        new_id = result["id"]
        MESSAGE_ID_FILE.write_text(new_id)
        print(f"Created message {new_id} ({len(servers)} servers)")


if __name__ == "__main__":
    main()
