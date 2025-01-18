"""
Bot for automated reposting from VKontakte community pages
to Telegram and Discord channels.

v1.0
by @stixanna
"""

import time

from loguru import logger

from config import SINGLE_START, TIME_TO_SLEEP
from start_script import start_script
from tools import prepare_temp_folder

# Лог для всех сообщений DEBUG и выше
logger.add(
    "./logs/debug.log",
    format="{time} {level} {message}",
    level="DEBUG",  # Записываются все логи
    rotation="1 month", # Триггер через месяц
)
# Лог только для WARNING и ERROR
logger.add(
    "./logs/warning_error.log",
    format="{time} {level} {message}",
    level="ERROR",  # Записываются только ERROR и выше
    rotation="1 MB",    # Триггер через месяц
    compression="zip",  # Сжать вместо удаления
)


logger.info("Script is started.")


@logger.catch
def main(firstStartBool):
    start_script(firstStartBool)
    prepare_temp_folder()

firstStartBool = True
while True:
    try:
        main(firstStartBool)
        firstStartBool = False
        if SINGLE_START:
            logger.info("Script has successfully completed its execution")
            exit()
        else:
            logger.info(f"Script went to sleep for {TIME_TO_SLEEP} seconds.")
            time.sleep(TIME_TO_SLEEP)
    except KeyboardInterrupt:
        logger.info("Script is stopped by the user.")
        exit()
