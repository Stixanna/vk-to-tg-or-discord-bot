import asyncio
import discord
from discord.ext import commands
import aiohttp
import io
import json

from aiogram import Bot, types
from aiogram.utils import exceptions
from loguru import logger

from tools import (split_text, 
                   clearTextExcludeLinks,
                   createTGlink,
                   convertToSendingFormat,
                   )


async def send_post(bot: Bot, tg_channel: str, text: str, photos: list, docs: list, tags: list, discord_token: str, discord_server_id: int, num_tries: int = 0) -> None:
    num_tries += 1
    if num_tries > 3:
        logger.error("Post was not sent to Telegram. Too many tries.")
        return
    try:
        if len(photos) == 0 and not docs:
            message = await send_text_post(bot, tg_channel, text)
        elif len(photos) == 1:
            message = await send_photo_post(bot, tg_channel, text, photos)
        elif len(photos) >= 2:
            message = await send_photos_post(bot, tg_channel, text, photos)
        elif docs:
            message = await send_docs_post(bot, tg_channel, text, docs)

        # Формируем ссылку на сообщение
        text = createTGlink(tg_channel, message, text)
        # Discord отправка (пример — отправляем текст и прикрепления)
        await send_to_discord(discord_token, discord_server_id, text, photos, docs, tags)

    except exceptions.RetryAfter as ex:
        logger.warning(f"Flood limit is exceeded. Sleep {ex.timeout} seconds. Try: {num_tries}")
        await asyncio.sleep(ex.timeout)
        await send_post(bot, tg_channel, text, photos, docs, num_tries)
    except exceptions.BadRequest as ex:
        logger.warning(f"Bad request. Wait 60 seconds. Try: {num_tries}. {ex}")
        await asyncio.sleep(60)
        await send_post(bot, tg_channel, text, photos, docs, num_tries)


async def send_text_post(bot: Bot, tg_channel: str, text: str) -> None:
    if not text:
        return

    if len(text) < 4096:
        message = await bot.send_message(tg_channel, text, parse_mode=types.ParseMode.HTML)
    else:
        text_parts = split_text(text, 4084)
        prepared_text_parts = (
            [text_parts[0] + " (...)"]
            + ["(...) " + part + " (...)" for part in text_parts[1:-1]]
            + ["(...) " + text_parts[-1]]
        )

        for part in prepared_text_parts:
            message = await bot.send_message(tg_channel, part, parse_mode=types.ParseMode.HTML)
            await asyncio.sleep(0.5)
    logger.info("Text post sent to Telegram.")
    return message


async def send_photo_post(bot: Bot, tg_channel: str, text: str, photos: list) -> None:
    if len(text) <= 1024:
        message = await bot.send_photo(tg_channel, photos[0], text, parse_mode=types.ParseMode.HTML)
        logger.info("Text post (<=1024) with photo sent to Telegram.")
    else:
        prepared_text = f'<a href="{photos[0]}"> </a>{text}'
        if len(prepared_text) <= 4096:
            message = await bot.send_message(tg_channel, prepared_text, parse_mode=types.ParseMode.HTML)
        else:
            await send_text_post(bot, tg_channel, text)
            message = await bot.send_photo(tg_channel, photos[0])
        logger.info("Text post (>1024) with photo sent to Telegram.")
    return message


async def send_photos_post(bot: Bot, tg_channel: str, text: str, photos: list) -> None:
    media = types.MediaGroup()
    for photo in photos:
        media.attach_photo(types.InputMediaPhoto(photo))

    if (len(text) > 0) and (len(text) <= 1024):
        media.media[0].caption = text
        media.media[0].parse_mode = types.ParseMode.HTML
    elif len(text) > 1024:
        await send_text_post(bot, tg_channel, text)
    message = await bot.send_media_group(tg_channel, media)
    logger.info("Text post with photos sent to Telegram.")
    return message


async def send_docs_post(bot: Bot, tg_channel: str, text: str, docs: list) -> None:
    for doc in docs:
        try:
            # Открываем файл из временной директории
            with open(f"./temp/{doc['title']}", "rb") as file:
                # Отправляем файл с текстом
                message = await bot.send_document(chat_id=tg_channel, document=file, caption=text)
                logger.info(f"Документ {doc['title']} отправлен в Telegram.")
            return message
        except Exception as e:
            logger.error(f"Ошибка при отправке документа {doc['title']}: {e}")



async def send_to_discord(
    discord_token: str,
    discord_server_id : int,
    text: str,
    photos: list,
    docs: list,
    tags: list,
) -> None:
    intents = discord.Intents.default()
    discord_bot = commands.Bot(command_prefix="!", intents=intents)
    text = clearTextExcludeLinks(text) # Не отправляем текст в дискорд кроме ссылок

    @discord_bot.event
    async def on_ready():
        try:
            # logger.info("Бот подключён!")

            # Получаем словарь вебхуков
            webhooks_dict = await get_webhooks(discord_bot, discord_server_id)

            for tag in tags:
                webhook = webhooks_dict.get(tag)

                if not webhook and '#other' in webhooks_dict:
                    if '#other' in tags:
                        continue
                    webhook = webhooks_dict['#other']  # Используем вебхук для "других" сообщений

                if webhook:
                    files = convertToSendingFormat(photos, docs) 
                    await send_discord_post( photos, text, files, webhook, discord_bot )
                else:
                    logger.warning(f"Вебхук для тега {tag} не найден, сообщение пропущено.")
        finally:
            await discord_bot.close()

    await discord_bot.start(discord_token)

# async def download_file(url: str) -> tuple[io.BytesIO, str]:
#     """Скачивает файл по URL и возвращает объект BytesIO и исправленное имя файла."""
#     async with aiohttp.ClientSession() as session:
#         async with session.get(url) as response:
#             if response.status == 200:
#                 data = await response.read()
#                 # logger.info(f"{url} url")
#                 original_filename = url.split("/")[-1]
#                 fixed_filename = fix_filename(original_filename)
#                 return io.BytesIO(data), fixed_filename
#             else:
#                 raise ValueError(f"Не удалось скачать файл: {url} (status: {response.status})")
            
async def get_webhooks(discord_bot, server_id, num_tries: int = 0) -> dict:
    num_tries += 1
    webhooks_dict = {}

    if num_tries > 3:
        logger.error("Post was not sent to Discord. Too many tries.")
        return
    try:
        for guild in discord_bot.guilds:
            if server_id == guild.id:
                # logger.info(f"Сервер: {guild.name} (ID: {guild.id})")
                for channel in guild.text_channels:
                    try:
                        webhooks = await channel.webhooks()
                        for webhook in webhooks:
                            webhooks_dict[webhook.name] = {'channel_id' : channel.id, 'url' : webhook.url}  # Добавляем в словарь
                            # logger.info(f"Вебхук добавлен: {webhook.name} -> {webhook.url}") # debug
                    except discord.Forbidden:
                        logger.warning(f"Нет доступа к вебхукам канала {channel.name}")
                    except Exception as e:
                        logger.error(f"Ошибка при получении вебхуков для канала {channel.name}: {e}")
        logger.info(f"Сервер: {guild.name} (ID: {guild.id}), Словарь вебхуков: {webhooks_dict}")
        return webhooks_dict
    except Exception as e:
        logger.warning(f"{e}. Sleep {10} seconds. Try: {num_tries}")
        await asyncio.sleep(10)
        await get_webhooks(discord_bot, server_id)

# Из за ограничения discord, через хттп-вебхуки сервером принимается только первый файл, остальные файлы в этом запросе будут проигнорированы
async def send_discord_aiohttpRequest(text, files, webhook_url):
    logger.info(f"Отправляем сообщение в вебхук: {webhook_url}")
    payload = { "content": text }

    async with aiohttp.ClientSession() as session:
        form_data = aiohttp.FormData()
        form_data.add_field('payload_json', json.dumps(payload))
        for file_name, file_data in files:
            form_data.add_field(file_name, file_data[1], filename=file_data[0])
        
        async with session.post(webhook_url, data=form_data) as response:
            if response.status == 200:
                logger.info(f"Сообщение успешно отправлено в вебхук {webhook_url}")
            else:
                logger.error(f"Ошибка отправки в вебхук {webhook_url}: {response.status}")


# Отправка сообщения из под бота в канале
async def send_discord_channel(text, files, channel_id, discord_bot):
    logger.info(f"Отправляем сообщение в канал: {channel_id}")

    channel = discord_bot.get_channel(channel_id)
    await channel.send(content=text, files=files)
    logger.info(f"Message sent to channel {channel.name} in Discord")


# Отправка сообщения
async def send_discord_post( photos, text, files, webhook, discord_bot, num_tries: int = 0):
    num_tries += 1
    if num_tries > 3:
        logger.error("Post was not sent to Discord. Too many tries.")
        return
    try:
        if len(photos) > 1 :
            await send_discord_channel(text, files, webhook['channel_id'], discord_bot)
        else:
            await send_discord_aiohttpRequest(text, files, webhook['url'])
    except Exception as e:
        logger.warning(f"{e}. Sleep {30} seconds. Try: {num_tries}")
        await asyncio.sleep(30)
        await send_discord_post(photos, text, files, webhook, discord_bot, num_tries)