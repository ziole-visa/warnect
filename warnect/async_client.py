import asyncio
import inspect
from typing import Any, Callable, Optional

from .client import BaileysClient


class AsyncBaileysClient:
    """Async wrapper around :class:`BaileysClient`.

    Event callbacks may be regular functions or coroutine functions. Coroutine
    callbacks are scheduled on the running event loop; blocking calls are run in
    a worker thread via ``asyncio.to_thread``.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self._client = BaileysClient(*args, **kwargs)
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._handler_map: dict[str, list[tuple[Callable, Callable]]] = {}

    def on(self, event: str, callback: Callable) -> None:
        def handler(data: Any) -> None:
            if inspect.iscoroutinefunction(callback):
                loop = self._loop
                if loop is None:
                    return
                asyncio.run_coroutine_threadsafe(callback(data), loop)
            else:
                callback(data)

        self._client.on(event, handler)
        self._handler_map.setdefault(event, []).append((callback, handler))

    def off(self, event: str, callback: Callable) -> None:
        entries = self._handler_map.get(event, [])
        for original, handler in list(entries):
            if original is callback:
                self._client.off(event, handler)
                entries.remove((original, handler))
        self._handler_map[event] = entries

    async def start(self, wait: bool = True, timeout: Optional[float] = None) -> Any:
        self._loop = asyncio.get_running_loop()
        return await asyncio.to_thread(self._client.start, wait, timeout)

    async def request(self, cmd: str, timeout: Optional[float] = None, **params: Any) -> Any:
        return await asyncio.to_thread(self._client.request, cmd, timeout, **params)

    async def ping(self) -> Any:
        return await asyncio.to_thread(self._client.ping)

    async def send_text(self, jid: str, text: str) -> Any:
        return await asyncio.to_thread(self._client.send_text, jid, text)

    async def send_image(self, jid: str, **kwargs: Any) -> Any:
        return await asyncio.to_thread(self._client.send_image, jid, **kwargs)

    async def send_document(self, jid: str, path: str, **kwargs: Any) -> Any:
        return await asyncio.to_thread(self._client.send_document, jid, path, **kwargs)

    async def request_pairing_code(self, number: str, custom_code: Optional[str] = None) -> Any:
        return await asyncio.to_thread(self._client.request_pairing_code, number, custom_code)

    async def send_presence(self, jid: str, presence: str) -> Any:
        return await asyncio.to_thread(self._client.send_presence, jid, presence)

    async def send_read(self, jid: str, message_id: str, participant: Optional[str] = None) -> Any:
        return await asyncio.to_thread(self._client.send_read, jid, message_id, participant)

    async def download_media(self, message_id: str) -> bytes:
        return await asyncio.to_thread(self._client.download_media, message_id)

    async def send_reaction(self, jid: str, emoji: str, message_id: str, from_me: bool = False, participant: Optional[str] = None) -> Any:
        return await asyncio.to_thread(self._client.send_reaction, jid, emoji, message_id, from_me, participant)

    async def reply_message(self, jid: str, text: str, quoted_id: str) -> Any:
        return await asyncio.to_thread(self._client.reply_message, jid, text, quoted_id)

    async def send_reaction(self, jid: str, emoji: str, message_id: str, from_me: bool = False, participant: Optional[str] = None) -> Any:
        return await asyncio.to_thread(self._client.send_reaction, jid, emoji, message_id, from_me, participant)

    async def reply_message(self, jid: str, text: str, quoted_id: str) -> Any:
        return await asyncio.to_thread(self._client.reply_message, jid, text, quoted_id)

    async def group_create(self, subject: str, participants: list) -> Any:
        return await asyncio.to_thread(self._client.group_create, subject, participants)

    async def invoke(self, method: str, *args: Any) -> Any:
        return await asyncio.to_thread(self._client.invoke, method, *args)

    async def list_methods(self) -> list[str]:
        return await asyncio.to_thread(self._client.list_methods)

    async def health(self) -> Any:
        return await asyncio.to_thread(self._client.health)

    @property
    def connected(self) -> bool:
        return self._client.connected

    async def group_create(self, subject: str, participants: list) -> Any:
        return await asyncio.to_thread(self._client.group_create, subject, participants)

    async def group_update_subject(self, jid: str, subject: str) -> Any:
        return await asyncio.to_thread(self._client.group_update_subject, jid, subject)

    async def group_update_description(self, jid: str, description: str) -> Any:
        return await asyncio.to_thread(self._client.group_update_description, jid, description)

    async def group_add_participants(self, jid: str, participants: list) -> Any:
        return await asyncio.to_thread(self._client.group_add_participants, jid, participants)

    async def group_remove_participants(self, jid: str, participants: list) -> Any:
        return await asyncio.to_thread(self._client.group_remove_participants, jid, participants)

    async def group_promote(self, jid: str, participants: list) -> Any:
        return await asyncio.to_thread(self._client.group_promote, jid, participants)

    async def group_demote(self, jid: str, participants: list) -> Any:
        return await asyncio.to_thread(self._client.group_demote, jid, participants)

    async def group_leave(self, jid: str) -> Any:
        return await asyncio.to_thread(self._client.group_leave, jid)

    async def group_invite_code(self, jid: str) -> Any:
        return await asyncio.to_thread(self._client.group_invite_code, jid)

    async def group_revoke_invite(self, jid: str) -> Any:
        return await asyncio.to_thread(self._client.group_revoke_invite, jid)

    def command(self, name: str, aliases=(), priority: int = 0):
        return self._client.command(name, aliases=aliases, priority=priority)

    def middleware(self, func):
        return self._client.middleware(func)

    def enable_router(self):
        self._client.enable_router()

    async def get_groups(self, limit: int = 100) -> Any:
        return await asyncio.to_thread(self._client.get_groups, limit)

    async def get_profile_picture(self, jid: str, type: str = "image") -> Any:
        return await asyncio.to_thread(self._client.get_profile_picture, jid, type)

    async def is_on_whatsapp(self, number: str) -> Any:
        return await asyncio.to_thread(self._client.is_on_whatsapp, number)

    async def logout(self) -> Any:
        return await asyncio.to_thread(self._client.logout)

    async def stop(self) -> None:
        await asyncio.to_thread(self._client.stop)

    async def __aenter__(self) -> "AsyncBaileysClient":
        self._loop = asyncio.get_running_loop()
        return self

    async def __aexit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        await self.stop()
