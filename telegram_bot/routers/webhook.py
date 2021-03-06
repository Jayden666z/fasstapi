from urllib.parse import urljoin
from typing import Any, Dict
from fastapi import APIRouter, Body, Depends
from loguru import logger
from telegram_bot.dependencies import bot_dispatcher, telegram_bot
from telegram_bot.settings import settings
from aiogram import Dispatcher, Bot
from starlette.responses import Response
from aiogram.types import Update
from starlette.status import HTTP_200_OK

router = APIRouter()


@router.post('/hook')
async def webhook_handler(
        update_raw: Dict[str, Any] = Body(...),
        dp: Dispatcher = Depends(bot_dispatcher),
) -> Response:
    """Set route /hook with POST method will trigger this method."""
    telegram_update = Update(**update_raw)
    Dispatcher.set_current(dp)
    Bot.set_current(dp.bot)
    await dp.process_update(telegram_update)
    return Response(status_code=HTTP_200_OK)


@router.on_event("startup")
async def set_webhook() -> None:
    """
    Tell Telegram API about new webhook on app startup.

    We need to check current webhook url first, because Telegram API has
    strong rate limit for `set_webhook` method.
    """
    logger.info("Starting set_webhook...")
    bot = telegram_bot()
    webhook_endpoint = router.url_path_for('webhook_handler')
    url = urljoin(settings.TELEGRAM_BOT_WEBHOOK_ENDPOINT, webhook_endpoint)
    current_url = (await bot.get_webhook_info())["url"]
    if current_url != url:
        await bot.set_webhook(url=url)
        logger.warning("webhook updated!")


@router.on_event("shutdown")
async def disconnect_storage() -> None:
    """
    Close connection to storage.

    We don't use storage at this moment, but in future...
    """
    dispatcher = bot_dispatcher()
    await dispatcher.storage.close()
    await dispatcher.storage.wait_closed()