import os
import re

from loguru import logger
import discord


def blacklist_check(blacklist: list, text: str) -> bool:
    if blacklist:
        text_lower = text.lower()
        for black_word in blacklist:
            if black_word.lower() in text_lower:
                logger.info(f"Post was skipped due to the detection of blacklisted word: {black_word}.")
                return True

    return False


def whitelist_check(whitelist: list, text: str) -> bool:
    if whitelist:
        text_lower = text.lower()
        for white_word in whitelist:
            if white_word.lower() in text_lower:
                return False
        logger.info("The post was skipped because no whitelist words were found.")
        return True

    return False


def prepare_temp_folder():
    if "temp" in os.listdir():
        for root, dirs, files in os.walk("temp"):
            for file in files:
                os.remove(os.path.join(root, file))
    else:
        os.mkdir("temp")


def prepare_text_for_reposts(text: str, item: dict, item_type: str, group_name: str) -> str:
    if item_type == "post" and text:
        from_id = item["copy_history"][0]["from_id"]
        id = item["copy_history"][0]["id"]
        link_to_repost = f"https://vk.com/wall{from_id}_{id}"
        text = f'{text}\n\n<a href="{link_to_repost}"><b>REPOST ↓ {group_name}</b></a>'
    if item_type == "repost":
        from_id = item["from_id"]
        id = item["id"]
        link_to_repost = f"https://vk.com/wall{from_id}_{id}"
        text = f'<a href="{link_to_repost}"><b>REPOST ↓ {group_name}</b></a>\n\n{text}'

    return text


def prepare_text_for_html(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def add_urls_to_text(text: str, urls: list, videos: list) -> str:
    first_link = True
    urls = videos + urls

    if not urls:
        return text

    for url in urls:
        if url not in text:
            if first_link:
                text = f'<a href="{url}"> </a>{text}\n\n{url}' if text else url
                first_link = False
            else:
                text += f"\n{url}"
    return text


def split_text(text: str, fragment_size: int) -> list:
    fragments = []
    for fragment in range(0, len(text), fragment_size):
        fragments.append(text[fragment : fragment + fragment_size])
    return fragments


def reformat_vk_links(text: str) -> str:
    match = re.search("\[([\w.]+?)\|(.+?)\]", text)
    while match:
        left_text = text[: match.span()[0]]
        right_text = text[match.span()[1] :]
        matching_text = text[match.span()[0] : match.span()[1]]

        link_domain, link_text = re.findall("\[(.+?)\|(.+?)\]", matching_text)[0]
        text = left_text + f"""<a href="{f'https://vk.com/{link_domain}'}">{link_text}</a>""" + right_text
        match = re.search("\[([\w.]+?)\|(.+?)\]", text)

    return text

# *********************

def convert_to_FormDataFormat(doc_data):
    try:
        correct_filename = doc_data.get('title')

        temp_file_path = f'./temp/{correct_filename}'
        with open(temp_file_path, 'rb') as file_data:
            return ('file', (correct_filename, file_data.read()))
    except Exception as e:
        file_url = doc_data.get('url')
        logger.error(f"Ошибка при добавлении фото {file_url}: {e}")


def convert_to_DiscordBotFormat(doc_data):
    try:
        correct_filename = doc_data.get('title')

        temp_file_path = f'./temp/{correct_filename}'
        with open(temp_file_path, 'rb') as file_data:
            return discord.File(file_data, filename=correct_filename)
    except Exception as e:
        file_url = doc_data.get('url')
        logger.error(f"Ошибка при добавлении фото {file_url}: {e}")


def convertToSendingFormat(photos, docs):
    from parse_posts import (get_doc)
    
    files = []

    # Загружаем изображения
    for photo_url in photos:
        doc = get_doc({'url':photo_url})
        if len(photos) == 1:
            files.append(convert_to_FormDataFormat(doc))
        elif len(photos) > 1:
            files.append(convert_to_DiscordBotFormat(doc))
    
    # Берем документы ранее созданные методом get_doc из темп папки
    for doc in docs:
        files.append(convert_to_FormDataFormat(doc))
    
    return files


def clearTextExcludeLinks(text):
    # Регулярное выражение для поиска Markdown-ссылок [Текст ссылки](URL)
    markdown_pattern = r'\[([^\]]+)\]\((https?://[^\s]+)\)'

    # Регулярное выражение для поиска обычных URL
    url_pattern = r'https?://[^\s]+'

    # Сохраняем Markdown-ссылки
    markdown_links = re.findall(markdown_pattern, text)
    markdown_results = [f"[{text_part}]({url})" for text_part, url in markdown_links]

    # Удаляем Markdown-ссылки из текста
    text_without_markdown = re.sub(markdown_pattern, '', text)

    # Сохраняем оставшиеся обычные ссылки
    other_links = re.findall(url_pattern, text_without_markdown)

    # Объединяем Markdown и обычные ссылки
    all_links = markdown_results + other_links

    # Возвращаем только ссылки
    return '\n'.join(all_links)


def createTGlink(tg_channel, message, text):
    if isinstance(message, list):
        if not message:
            raise ValueError("Передан пустой список сообщений.")
        message = message[0]  # Берем первый элемент списка
    link = f"[Ссылка на телеграм пост](https://t.me/{tg_channel.lstrip('@')}/{message.message_id})"
    text = f"{text}\n{link}"
    return text
