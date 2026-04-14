"""
Telegram Audio Transcriber
--------------------------
Downloads voice/audio messages from a Telegram chat and transcribes them
using OpenAI Whisper API.

Setup:
  1. Copy .env.example → .env and fill in your credentials
  2. pip install -r requirements.txt
  3. python transcribe.py --chat "Username or chat name"

First run: Telegram will ask for your phone number + verification code.
Session is saved locally so you only log in once.
"""

import os
import sys
import asyncio
import argparse
from pathlib import Path
from datetime import datetime

from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.tl.types import MessageMediaDocument, MessageMediaVoice
import openai

load_dotenv()

# ── Config ────────────────────────────────────────────────────────────────────

API_ID       = int(os.environ["TELEGRAM_API_ID"])
API_HASH     = os.environ["TELEGRAM_API_HASH"]
OPENAI_KEY   = os.environ["OPENAI_API_KEY"]
SESSION_FILE = "telegram_session"
AUDIO_DIR    = Path("downloads")
OUTPUT_FILE  = Path("transcriptions.txt")

AUDIO_MIME_TYPES = {
    "audio/ogg", "audio/mpeg", "audio/mp4",
    "audio/wav", "audio/x-wav", "audio/webm",
    "audio/flac", "audio/aac",
}

# ── Helpers ───────────────────────────────────────────────────────────────────

def is_audio_message(msg) -> bool:
    """Return True if the message contains a voice note or audio file."""
    if not msg.media:
        return False
    if isinstance(msg.media, MessageMediaVoice):
        return True
    if isinstance(msg.media, MessageMediaDocument):
        doc = msg.media.document
        if doc.mime_type in AUDIO_MIME_TYPES:
            return True
        for attr in doc.attributes:
            if attr.__class__.__name__ in ("DocumentAttributeAudio",
                                           "DocumentAttributeVoice"):
                return True
    return False


def ext_for_message(msg) -> str:
    """Pick a reasonable file extension for the audio message."""
    if isinstance(msg.media, MessageMediaVoice):
        return ".ogg"
    if isinstance(msg.media, MessageMediaDocument):
        mime = msg.media.document.mime_type
        return {
            "audio/ogg":  ".ogg",
            "audio/mpeg": ".mp3",
            "audio/mp4":  ".m4a",
            "audio/wav":  ".wav",
            "audio/flac": ".flac",
            "audio/aac":  ".aac",
        }.get(mime, ".ogg")
    return ".ogg"


async def download_audio_messages(client, chat, limit: int, output_dir: Path):
    """Fetch messages from *chat* and download the audio ones."""
    output_dir.mkdir(exist_ok=True)
    downloaded = []

    print(f"\nScanning messages from: {chat}")
    async for msg in client.iter_messages(chat, limit=limit):
        if not is_audio_message(msg):
            continue

        ts  = msg.date.strftime("%Y%m%d_%H%M%S")
        ext = ext_for_message(msg)
        filename = output_dir / f"{ts}_{msg.id}{ext}"

        if filename.exists():
            print(f"  [skip] {filename.name} (already downloaded)")
        else:
            print(f"  [down] {filename.name}")
            await client.download_media(msg, file=str(filename))

        downloaded.append((msg, filename))

    return downloaded


def transcribe_file(path: Path, language: str | None, client: openai.OpenAI) -> str:
    """Send *path* to Whisper and return the transcription text."""
    kwargs = {"model": "whisper-1", "response_format": "text"}
    if language:
        kwargs["language"] = language

    with open(path, "rb") as f:
        result = client.audio.transcriptions.create(file=f, **kwargs)

    return result.strip()


# ── Main ──────────────────────────────────────────────────────────────────────

async def main(chat: str, limit: int, language: str | None, skip_download: bool):
    openai_client = openai.OpenAI(api_key=OPENAI_KEY)

    async with TelegramClient(SESSION_FILE, API_ID, API_HASH) as tg:
        if skip_download:
            # Use whatever is already in downloads/
            files = sorted(AUDIO_DIR.glob("*"))
            pairs = [(None, f) for f in files if f.is_file()]
        else:
            pairs = await download_audio_messages(tg, chat, limit, AUDIO_DIR)

    if not pairs:
        print("No audio messages found.")
        return

    print(f"\nTranscribing {len(pairs)} file(s) …")
    results = []

    for msg, path in pairs:
        print(f"  {path.name} … ", end="", flush=True)
        try:
            text = transcribe_file(path, language, openai_client)
            print("done")
        except Exception as e:
            text = f"[ERROR: {e}]"
            print(f"ERROR — {e}")

        timestamp = msg.date.strftime("%Y-%m-%d %H:%M:%S") if msg else path.stem[:15]
        sender    = "?" if msg is None else (
            getattr(msg.sender, "first_name", "") or
            getattr(msg.sender, "username", "unknown")
        )
        results.append((timestamp, sender, path.name, text))

    # Write output
    with open(OUTPUT_FILE, "w", encoding="utf-8") as out:
        out.write(f"# Telegram Audio Transcriptions\n")
        out.write(f"# Chat : {chat}\n")
        out.write(f"# Date : {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")
        for ts, sender, fname, text in results:
            out.write(f"---\n")
            out.write(f"[{ts}] {sender}  ({fname})\n")
            out.write(f"{text}\n\n")

    print(f"\nSaved {len(results)} transcription(s) → {OUTPUT_FILE}")

    # Also print to stdout
    print("\n" + "=" * 60)
    for ts, sender, fname, text in results:
        print(f"\n[{ts}] {sender}")
        print(text)
    print("=" * 60)


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Download & transcribe Telegram voice messages."
    )
    parser.add_argument(
        "--chat", required=False, default=None,
        help="Telegram username, phone number, or chat name (e.g. @username)",
    )
    parser.add_argument(
        "--limit", type=int, default=100,
        help="Max number of messages to scan (default: 100)",
    )
    parser.add_argument(
        "--language", default=None,
        help="Language hint for Whisper, e.g. 'ru', 'en' (auto-detect if omitted)",
    )
    parser.add_argument(
        "--skip-download", action="store_true",
        help="Skip Telegram download; transcribe files already in downloads/",
    )
    args = parser.parse_args()

    if not args.skip_download and not args.chat:
        parser.error("--chat is required unless --skip-download is used")

    asyncio.run(main(args.chat, args.limit, args.language, args.skip_download))
