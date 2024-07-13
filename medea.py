import os
import subprocess as sp
import shutil
import requests
import json
import discord
from discord.ext import commands
from discord import app_commands
from time import sleep
from bing_image_downloader import downloader
from llm_chat import *

class Bot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.all()
        intents.message_content = True
        super().__init__(command_prefix=".", intents=intents)
    
    async def setup_hook(self):
        await self.tree.sync(guild = discord.Object(id = 1155948125077381141))
        await self.tree.sync(guild = discord.Object(id = 1172869573473742928))
        print(f"Synced slash command for {self.user}.")

def init_chats(chats, current_chat):
    for chatname in os.listdir("chats"):
        chats[chatname] = access_ollama(message_file=f"chats/{chatname}")

    with open("current_chat.txt", 'r') as c:
        current_chat = c.read()
    return chats, current_chat

def get_chunks(s, maxlength):
    start = 0
    end = 0
    while start + maxlength  < len(s) and end != -1:
        end = s.rfind("\n", start, start + maxlength + 1)
        yield s[start:end]
        start = end +1
    yield s[start:]

if __name__ == "__main__":

    # bot = commands.Bot(command_prefix=".", intents=discord.Intents.all())
    bot = Bot()

    chats = {}
    current_chat = None
    chats, current_chat = init_chats(chats, current_chat)

    @bot.hybrid_command(name="hello", with_app_command=True, description="Displays hello message.\nCommand: .hello")
    @app_commands.guilds(discord.Object(id = 1155948125077381141), discord.Object(id = 1172869573473742928))
    async def hello(ctx):
        await ctx.reply("Hello! I'm Medea.")
        
    @bot.hybrid_command(name="welcome", with_app_command=True, description="Displays welcome message.\nCommand: .welcome")
    @app_commands.guilds(discord.Object(id = 1155948125077381141), discord.Object(id = 1172869573473742928))
    async def welcome(ctx):
        await ctx.reply(f"Hello {ctx.author.display_name}! Welcome to discord.")

    @bot.hybrid_command(name="suggest", with_app_command=True, description="Top bing image result for the given query (Username in case of no query.)\nCommand: .suggest <query>")
    @app_commands.guilds(discord.Object(id = 1155948125077381141), discord.Object(id = 1172869573473742928))
    async def suggest(ctx, *, query=None):
        async with ctx.typing():
            if not query:
                query = ctx.author.display_name
            downloader.download(str(query), limit=1, output_dir='dataset', adult_filter_off=False, force_replace=False, timeout=60, verbose=True)
            dir = os.listdir(f"dataset/{query}")
        if len(dir) == 0:
            await ctx.reply(f"No image found in bing for {query}")
        else:
            for image in dir:
                await ctx.reply(f"Top bing image result for {query}", file=discord.File(f"dataset/{query}/{image}"))
        shutil.rmtree(f"dataset/{query}")

    @bot.hybrid_command(name="chatlist", with_app_command=True, description="Returns the list of available chats.\nCommand: .chatlist")
    @app_commands.guilds(discord.Object(id = 1155948125077381141), discord.Object(id = 1172869573473742928))
    async def chatlist(ctx):
        global chats, current_chat
        if len(chats) == 0:
            await ctx.reply("No available chat.")
        else:
            s = "\n".join(list(chats))
            await ctx.reply(f"Available chats: \n{s}")

    @bot.hybrid_command(name="chatselect", with_app_command=True, description="Sets the given chat as current chat.\nCommand: .chatselect <chat name>")
    @app_commands.guilds(discord.Object(id = 1155948125077381141), discord.Object(id = 1172869573473742928))
    async def chatselect(ctx, *, arg:str):
        global chats, current_chat
        async with ctx.typing():
            if arg in chats:
                with open("current_chat.txt", 'w') as c:
                    c.write(arg)
                chats, current_chat = init_chats(chats, current_chat)
                await ctx.reply(f"Current chat changed to {current_chat}")
            else:
                await ctx.reply(f"No available chat with name: {arg}")
    
    @bot.hybrid_command(name="chatnew", with_app_command=True, description="Starts a new chat with the given name.\n(*chat name is required)\nCommand: .chatnew <chat name>")
    @app_commands.guilds(discord.Object(id = 1155948125077381141), discord.Object(id = 1172869573473742928))
    async def chatnew(ctx, *, arg:str):
        global chats, current_chat
        async with ctx.typing():
            if len(list(chats)) >= 16:
                s = "\n".join(list(chats))
                await ctx.reply(f"Total number of chats is capped at 16. There are already 16 chats present, new chat cannot be created.\nDelete previous chats to create a new one.\nAvailable chats: {s}\n\nContact the bot developer to increase the maximum number of chats")
            else:
                if (not arg) or arg == "":
                    await ctx.reply("*chat name is required. No chat name given.")
                elif arg in chats:
                    await ctx.reply("Chat with specified name already present.")
                else:
                    with open(f"chats/{arg}", 'a') as a:
                        pass
                    with open("current_chat.txt", 'w') as c:
                        c.write(arg)
                    chats, current_chat = init_chats(chats, current_chat)
                    await ctx.reply(f"Current chat changed to {current_chat}")

    @bot.hybrid_command(name="chat", with_app_command=True, description="Resumes the last chat.\nCommand: .chat <your response>")
    @app_commands.guilds(discord.Object(id = 1155948125077381141), discord.Object(id = 1172869573473742928))
    async def chat(ctx, *, arg: str):
        global chats, current_chat
        async with ctx.typing():
            if current_chat != "":
                # print("You: ", arg)
                response = chats[current_chat].input_handler(arg)
                # print("AI: ", response)
                if response:
                    responses = get_chunks(response, 1000)
                    for r in responses:
                        await ctx.send(r)
            else:
                await ctx.reply("No current chat record.\nEither last chat is deleted or no available chat.\nStart a new chat by .chatnew <chat name>\nor\nSelect an available chat by .chatselect <chat name>")

    @bot.hybrid_command(name="chatdel", with_app_command=True, description="Deletes the specified chat.\n(Current chat in case no chat name given.)\nCommand: .chatdel <chat name>")
    @app_commands.guilds(discord.Object(id = 1155948125077381141), discord.Object(id = 1172869573473742928))
    async def chatdel(ctx, *, arg:str):
        global chats, current_chat
        async with ctx.typing():
            if (not arg) or arg == "":
                arg = current_chat
            if arg in chats:
                os.remove(f"chats/{arg}")
                await ctx.send("Specified chat has been deleted.\nStart a new chat by .chatnew <chat name>\nor\nSelect an available chat by .chatselect <chat name>")
                if current_chat == arg:
                    with open("current_chat.txt", 'w') as c:
                        pass
                    await ctx.send("No current chat. ")
                chats, current_chat = init_chats(chats, current_chat)
            else:
                await ctx.reply(f"No available chat with name: {arg}")

    @bot.hybrid_command(name="run", with_app_command=True, description="Runs the specified command on the shell terminal\nCommand: .run <command>")
    @app_commands.guilds(discord.Object(id = 1155948125077381141), discord.Object(id = 1172869573473742928))
    async def run(ctx, *, arg:str):
        if ctx.message.author.id == 768688041820422156:
            async with ctx.typing():
                result = sp.run(arg, capture_output=True, shell=True, text=True).stdout
                if result != None:
                    result += "\n\nCommand run successfully"
                    results = get_chunks(result, 1000)
                    for r in results:
                        await ctx.reply(r)
        else:
            await ctx.reply("This function is only available to the bot developer. Contact him for further details.")

    token = "MTI0OTA3NjQzNzUxMjYxODAxNA.GZDMrM.uQdGpj2nexOoZDo74VNrYwoNchNMedQo5-B8Ro"
    bot.run(token)
