import asyncio
import logging
from typing import Optional
from app.config import settings
from app.integrations.base import SocialIntegration

logger = logging.getLogger(__name__)


class TelegramIntegration(SocialIntegration):
    platform = "telegram"

    def get_oauth_url(self, state: Optional[str] = None) -> str:
        raise NotImplementedError("Telegram uses phone-based auth, not OAuth URL")

    async def exchange_code(self, code: str, state: Optional[str] = None) -> dict:
        raise NotImplementedError("Use phone-based auth flow")

    async def start_phone_auth(self, phone: str) -> dict:
        """Initiate phone authentication. Returns session string and phone_code_hash."""
        try:
            from telethon import TelegramClient
            from telethon.sessions import StringSession
        except ImportError:
            raise RuntimeError("telethon is not installed")

        api_id = int(settings.TELEGRAM_API_ID)
        api_hash = settings.TELEGRAM_API_HASH

        proxy = None
        if settings.PROXY_HOST and settings.PROXY_PORT:
            import socks
            proxy = (socks.SOCKS5, settings.PROXY_HOST, settings.PROXY_PORT)
            if settings.PROXY_USER:
                proxy = (socks.SOCKS5, settings.PROXY_HOST, settings.PROXY_PORT,
                         True, settings.PROXY_USER, settings.PROXY_PASSWORD)

        client = TelegramClient(StringSession(), api_id, api_hash, proxy=proxy)
        await client.connect()
        result = await client.send_code_request(phone)
        session_str = client.session.save()
        await client.disconnect()
        return {"session": session_str, "phone_code_hash": result.phone_code_hash}

    async def complete_phone_auth(self, phone: str, code: str, session: str, phone_code_hash: str) -> str:
        """Complete phone auth, return new session string."""
        try:
            from telethon import TelegramClient
            from telethon.sessions import StringSession
        except ImportError:
            raise RuntimeError("telethon is not installed")

        api_id = int(settings.TELEGRAM_API_ID)
        api_hash = settings.TELEGRAM_API_HASH

        client = TelegramClient(StringSession(session), api_id, api_hash)
        await client.connect()
        await client.sign_in(phone, code, phone_code_hash=phone_code_hash)
        session_str = client.session.save()
        await client.disconnect()
        return session_str

    async def publish_post(
        self,
        token: str,
        content: str,
        media_urls: Optional[list[str]] = None,
        extra: Optional[dict] = None,
    ) -> str:
        try:
            from telethon import TelegramClient
            from telethon.sessions import StringSession
        except ImportError:
            raise RuntimeError("telethon is not installed")

        api_id = int(settings.TELEGRAM_API_ID)
        api_hash = settings.TELEGRAM_API_HASH
        channel = (extra or {}).get("channel")
        if not channel:
            raise ValueError("Telegram extra must contain 'channel'")

        client = TelegramClient(StringSession(token), api_id, api_hash)
        await client.connect()
        try:
            from app.core.media_uploader import download_media
            if media_urls:
                files = []
                for url in media_urls:
                    data, ct = await download_media(url)
                    files.append(data)
                msg = await client.send_file(channel, files, caption=content)
            else:
                msg = await client.send_message(channel, content)
            return str(msg.id)
        finally:
            await client.disconnect()

    async def get_post_stats(
        self, token: str, post_id: str, extra: Optional[dict] = None
    ) -> dict:
        try:
            from telethon import TelegramClient
            from telethon.sessions import StringSession
            from telethon.tl.functions.channels import GetMessagesRequest
        except ImportError:
            raise RuntimeError("telethon is not installed")

        api_id = int(settings.TELEGRAM_API_ID)
        api_hash = settings.TELEGRAM_API_HASH
        channel = (extra or {}).get("channel")
        if not channel:
            return {"likes": 0, "views": 0, "shares": 0, "comments": 0, "reach": 0}

        client = TelegramClient(StringSession(token), api_id, api_hash)
        await client.connect()
        try:
            msgs = await client.get_messages(channel, ids=[int(post_id)])
            msg = msgs[0] if msgs else None
            views = getattr(msg, "views", 0) or 0
            forwards = getattr(msg, "forwards", 0) or 0
            return {"likes": 0, "views": views, "shares": forwards, "comments": 0, "reach": views}
        finally:
            await client.disconnect()


telegram_integration = TelegramIntegration()
