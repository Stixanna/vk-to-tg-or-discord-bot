import asyncio
import discord
from discord.ext import commands
import aiohttp
import io

from aiogram import Bot, types
from aiogram.utils import exceptions
from loguru import logger

from tools import split_text, fix_filename


async def send_post(bot: Bot, tg_channel: str, text: str, photos: list, docs: list, tags: list, discord_token: str, num_tries: int = 0) -> None:
    num_tries += 1
    if num_tries > 3:
        logger.error("Post was not sent to Telegram. Too many tries.")
        return
    try:
        if len(photos) == 0 and not docs:
            await send_text_post(bot, tg_channel, text)
        elif len(photos) == 1:
            await send_photo_post(bot, tg_channel, text, photos)
        elif len(photos) >= 2:
            await send_photos_post(bot, tg_channel, text, photos)
        elif docs:
            await send_docs_post(bot, tg_channel, text, docs)
        # Discord отправка (пример — отправляем текст и прикрепления)
        await send_to_discord(discord_token, text, photos, docs, tags)

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
        await bot.send_message(tg_channel, text, parse_mode=types.ParseMode.HTML)
    else:
        text_parts = split_text(text, 4084)
        prepared_text_parts = (
            [text_parts[0] + " (...)"]
            + ["(...) " + part + " (...)" for part in text_parts[1:-1]]
            + ["(...) " + text_parts[-1]]
        )

        for part in prepared_text_parts:
            await bot.send_message(tg_channel, part, parse_mode=types.ParseMode.HTML)
            await asyncio.sleep(0.5)
    logger.info("Text post sent to Telegram.")


async def send_photo_post(bot: Bot, tg_channel: str, text: str, photos: list) -> None:
    if len(text) <= 1024:
        await bot.send_photo(tg_channel, photos[0], text, parse_mode=types.ParseMode.HTML)
        logger.info("Text post (<=1024) with photo sent to Telegram.")
    else:
        prepared_text = f'<a href="{photos[0]}"> </a>{text}'
        if len(prepared_text) <= 4096:
            await bot.send_message(tg_channel, prepared_text, parse_mode=types.ParseMode.HTML)
        else:
            await send_text_post(bot, tg_channel, text)
            await bot.send_photo(tg_channel, photos[0])
        logger.info("Text post (>1024) with photo sent to Telegram.")


async def send_photos_post(bot: Bot, tg_channel: str, text: str, photos: list) -> None:
    media = types.MediaGroup()
    for photo in photos:
        media.attach_photo(types.InputMediaPhoto(photo))

    if (len(text) > 0) and (len(text) <= 1024):
        media.media[0].caption = text
        media.media[0].parse_mode = types.ParseMode.HTML
    elif len(text) > 1024:
        await send_text_post(bot, tg_channel, text)
    await bot.send_media_group(tg_channel, media)
    logger.info("Text post with photos sent to Telegram.")


async def send_docs_post(bot: Bot, tg_channel: str, text: str, docs: list) -> None:
    for doc in docs:
        try:
            # Открываем файл из временной директории
            with open(f"./temp/{doc['title']}", "rb") as file:
                # Отправляем файл с текстом
                await bot.send_document(chat_id=tg_channel, document=file, caption=text)
                logger.info(f"Документ {doc['title']} отправлен в Telegram.")
        except Exception as e:
            logger.error(f"Ошибка при отправке документа {doc['title']}: {e}")



async def send_to_discord(
    discord_token: str,
    text: str,
    photos: list,
    docs: list,
    tags: list,
) -> None:
    intents = discord.Intents.default()
    discord_bot = commands.Bot(command_prefix="!", intents=intents)
    @discord_bot.event
    async def on_ready():
        try:
            # logger.info("Бот подключён!")
            # for guild in bot.guilds:
            #     logger.info(f"Сервер: {guild.name} (ID: {guild.id})")
            #     for channel in guild.channels:
            #         logger.info(f"Канал: {channel.name} (ID: {channel.id})")

            for tag in tags:
                match tag:
                    case '#dota':
                        channel_id = 277493272346230785  # Замените ID канала
                    case _:
                        continue    # Если такого тега нет, то пропускаем пост, не отправляем (надо дописать - если никаких тегов нет то отправить хоть кудато)
                        # channel_id = 1315308603527397476  # Замените ID канала
                channel = discord_bot.get_channel(channel_id)
                if channel:
                    logger.info(f"Найден канал {channel.name}, отправляем сообщение.")

                    files = []  # Список файлов для прикрепления

                    # Добавляем изображения
                    for photo_url in photos:
                        try:
                            photo_data, filename = await download_file(photo_url)
                            files.append(discord.File(photo_data, filename=filename))
                        except Exception as e:
                            logger.error(f"Ошибка при добавлении фото {photo_url}: {e}")

                    # Добавляем документы
                    for doc in docs:
                        try:
                            # Если doc — это словарь с URL, скачиваем файл
                            if isinstance(doc, dict) and 'url' in doc:
                                doc_data, filename = await download_file(doc['url'])
                                filename = doc.get('title', filename)  # Используем заголовок, если указан
                                files.append(discord.File(doc_data, filename=filename))
                            elif isinstance(doc, str):
                                # Если doc — это строка, предполагаем, что это локальный путь
                                files.append(discord.File(doc))
                            else:
                                raise ValueError(f"Неверный формат данных: {doc}")
                        except Exception as e:
                            logger.error(f"Ошибка при добавлении документа {doc}: {e}")

                    # Отправляем сообщение с текстом и вложениями
                    await channel.send(content=text, files=files)
                    logger.info(f"Message sent to channel {channel.name} in Discord")
                else:
                    logger.error(f"Канал с ID {channel_id} не найден.")
        finally:
            await discord_bot.close()

    await discord_bot.start(discord_token)

async def download_file(url: str) -> tuple[io.BytesIO, str]:
    """Скачивает файл по URL и возвращает объект BytesIO и исправленное имя файла."""
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.read()
                # logger.info(f"{url} url")
                original_filename = url.split("/")[-1]
                fixed_filename = fix_filename(original_filename)
                return io.BytesIO(data), fixed_filename
            else:
                raise ValueError(f"Не удалось скачать файл: {url} (status: {response.status})")
