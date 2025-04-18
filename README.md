<h1 align="center">vk-to-tg-or-discord-bot</h1>
<p align=center>
    <a target="_blank" href="https://www.python.org/downloads/" title="Python Version"><img src="https://img.shields.io/badge/python-%3E=_3.8-purple.svg"></a>
    <a target="_blank" href="https://github.com/alcortazzo/vktgbot/releases"><img alt="docker image" src="https://img.shields.io/github/v/release/alcortazzo/vktgbot?include_prereleases"></a>
    <a target="_blank" href="LICENSE" title="License: GPL-3.0"><img src="https://img.shields.io/github/license/alcortazzo/vktgbot.svg?color=red"></a>
</p> 

<p align="center"><b>Telegram bot for automatic forwarding posts from VK to Telegram, optional to Discord.</b></p>

<p align="center">
    <a href="https://youtu.be/59_-yB5WjnI">
        <img src="https://github.com/alcortazzo/vktgbot/blob/master/images/code.png"/>
    </a>
</p>

## About

Python script to automatically repost from VK community pages to Telegram channels or chats. Once the script is set up and running, it will check for new posts in VK every *N* seconds using VK API and, if there are any, parse and send them to Telegram.

## How to use the script

You can manually run the script with Python or Docker and leave it running in the background. Or you can set the script to run automatically on the remote server with tools like crontab, systemd, etc. Or you can configure the script to run at one time if you set `VAR_SINGLE_START = True` in `.env` file.

## Installation
```shell
# clone the repository
$ git clone https://github.com/alcortazzo/vktgbot.git

# if you want to clone specific version (for example v2.6)
$ git clone -b v2.6 https://github.com/alcortazzo/vktgbot.git

# change the working directory to vktgbot
$ cd vktgbot
```
*Note that in version 3.0 the script has been rewritten from the [pyTelegramBotAPI](https://github.com/eternnoir/pyTelegramBotAPI) library to the [aiogram](https://github.com/aiogram/aiogram) library. So if you want to install an older version of the script working with the pyTelegramBotAPI library, install version 2.6 using the method above. You can find instructions on how to run an older version of the script [here](https://github.com/alcortazzo/vktgbot/tree/v2.6).*

## Configuring
**Create file `.env` near `env.example` and copy all inside**
**Open `.env` configuration file with text editor and set the following variables:**
```ini
VAR_TG_CHANNEL = @aaaa
VAR_TG_BOT_TOKEN = 1234567890:AAA-AaA1aaa1AAaaAa1a1AAAAA-a1aa1-Aa
VAR_VK_TOKEN = 00a0a0ab00f0a0ab00f0a6ab0c00000b0f000f000f0a0ab0a00b000000dd00000000de0
VAR_VK_DOMAIN = bbbb
VAR_DISCORDSERVER_ID = 1234567890 
VAR_DISCORDBOT_TOKEN = 00a0a0ab00f0a0ab00f0a6ab0c00000b0f000f000f0a0ab0a00b000000dd00000000de0
```
* `VAR_TG_CHANNEL` is link or ID of Telegram channel. **You must add bot to this channel as an administrator!**
* `VAR_TG_BOT_TOKEN` is token for your Telegram bot. You can get it here: [BotFather](https://t.me/BotFather).
* `VAR_VK_TOKEN` is personal token for your VK profile. You can get it here: [HowToGet](https://github.com/alcortazzo/vktgbot/wiki/How-to-get-personal-access-token).
* `VAR_VK_DOMAIN` is part of the link (after vk.com/) to the VK channel. For example, if link is `vk.com/durov`, you should set `VAR_VK_DOMAIN = durov`.
* `VAR_DISCORDSERVER_ID` # discord reply is optional, no variable => no reply.
* `VAR_DISCORDBOT_TOKEN` need to add this your bot to discord_server(VAR_DISCORDSERVER_ID).

**Need to set-up webhooks in discord_server(VAR_DISCORDSERVER_ID) for correct bot work:**
* Go in your Discord text_channels and set up webhooks in channel named like `#tag_name` to bot sort posts by tags
* If post have no tags, script will try to find text_channel with webhook named `#other`
* If discord_server(VAR_DISCORDSERVER_ID) has no webhook named `#other`, post will not send

## Running
### Using Python
```shell
# install requirements
$ python3 -m pip install -r requirements.txt

# run script
$ python3 vktgbot
```
### Using Docker
```shell
# change the working directory to docker
$ cd docker

# build and run docker
$ docker-compose up --build
```
* If need many bots, create `.env` file near `docker-compose.yml` and set the following variable, it let set unique container-name:
```ini
APP_NAME = container-name
```
## License
GPLv3<br/>
Original Creator - [alcortazzo](https://github.com/alcortazzo)
