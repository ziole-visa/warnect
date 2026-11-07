import asyncio
import inspect
from typing import Any, Callable, Optional

DEFAULT_PREFIX = "."


class MessageContext:
    def __init__(self, client, event, async_mode: bool = False):
        self.client = client
        self.event = event
        self.async_mode = async_mode

    @property
    def text(self) -> str:
        return str(self.event.get("text") or "")

    @property
    def chat(self) -> Optional[str]:
        return self.event.get("chat")

    @property
    def sender(self) -> Optional[str]:
        return self.event.get("sender")

    @property
    def is_group(self) -> bool:
        return bool(self.event.get("isGroup"))

    def reply_sync(self, text: str) -> Any:
        if not self.chat:
            raise ValueError("no chat available")
        return self.client.send_text(self.chat, text)

    async def reply(self, text: str) -> Any:
        if self.async_mode:
            return await self.client.send_text(self.chat, text)
        return self.reply_sync(text)

    def download_media_sync(self) -> bytes:
        msg_id = self.event.get("id")
        if not msg_id:
            raise ValueError("message has no id")
        return self.client.download_media(msg_id)

    async def download_media(self) -> bytes:
        if self.async_mode:
            return await self.client.download_media(self.event.get("id"))
        return self.download_media_sync()


class CommandRouter:
    def __init__(self, client, prefix: str = DEFAULT_PREFIX):
        self.client = client
        self.prefix = prefix
        self._commands: dict[str, dict] = {}
        self._middlewares: list[Callable] = []
        self.enabled = False

    def command(self, name: str, aliases=(), priority: int = 0):
        def decorator(func):
            entry = {"name": name, "func": func, "aliases": list(aliases), "priority": priority}
            self._commands[name] = entry
            for alias in aliases:
                self._commands[alias] = entry
            self.enabled = True
            return func

        return decorator

    def middleware(self, func):
        self._middlewares.append(func)
        self.enabled = True
        return func

    def enable(self):
        self.enabled = True

    def _parse(self, text: str):
        text = (text or "").strip()
        if not text.startswith(self.prefix):
            return None, []
        parts = text[len(self.prefix):].split()
        if not parts:
            return None, []
        return parts[0].lower(), parts[1:]

    def dispatch(self, event):
        if not self.enabled:
            return
        text = event.get("text") if hasattr(event, "get") else None
        name, args = self._parse(text or "")
        if not name:
            return
        entry = self._commands.get(name)
        if not entry:
            return
        ctx = MessageContext(self.client, event, async_mode=False)
        # run middlewares
        for mw in self._middlewares:
            try:
                result = mw(ctx)
                if inspect.iscoroutine(result):
                    result = asyncio.run(result)
                if result is False:
                    return
            except Exception as exc:
                self.client.logger.exception("middleware error: %s", exc)
                return
        try:
            func = entry["func"]
            if inspect.iscoroutinefunction(func):
                asyncio.run(func(ctx))
            else:
                func(ctx)
        except Exception as exc:
            self.client.logger.exception("command %s failed: %s", name, exc)
            try:
                ctx.reply_sync(f"❌ Error: {exc}")
            except Exception:
                pass
