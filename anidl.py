# import discord
# from discord.ext import commands
# from discord import app_commands
from anipy_api.provider import list_providers, get_provider, LanguageTypeEnum
from anipy_api.anime import Anime
# from pathlib import Path
from anipy_api.download import Downloader
# from wrapt_timeout_decorator import timeout
import subprocess as sp
from time import sleep

provider = get_provider("gogoanime")
results = provider.get_search("boruto")
animes = []
for r in results:
    animes.append(Anime.from_search_result(provider, r))

# print("\n".join([anime.name for anime in animes]))

anime = animes[1]
info = anime.get_info()
print(info.name)

episodes = anime.get_episodes(lang=LanguageTypeEnum.SUB)
print(len(episodes))
