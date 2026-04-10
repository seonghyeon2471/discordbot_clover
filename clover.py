import discord
from discord.ext import commands
from discord.utils import get
import json
import os
import random
import sys
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_CLOVERTOKEN")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="이!", intents=intents, help_command=None)

CONFIG_FILE = "/tmp/naru_config.json"
STATUS_FILE = "/tmp/naru_status.json"
TARGET_CHANNEL_ID = None
counting_active = False
message_list = []
reacted_messages = []

def save_status():
    status = {
        "botUsername": str(bot.user) if bot.user else None,
        "targetChannelId": str(TARGET_CHANNEL_ID) if TARGET_CHANNEL_ID else None,
        "targetChannelName": None,
        "countingActive": counting_active,
        "messageCount": len(message_list),
        "reactedCount": len(reacted_messages),
    }
    if TARGET_CHANNEL_ID and bot.is_ready():
        for guild in bot.guilds:
            ch = guild.get_channel(TARGET_CHANNEL_ID)
            if ch:
                status["targetChannelName"] = ch.name
                break
    with open(STATUS_FILE, "w") as f:
        json.dump(status, f)

if os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE, "r") as f:
        data = json.load(f)
        TARGET_CHANNEL_ID = data.get("TARGET_CHANNEL_ID")

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}', flush=True)
    save_status()

@bot.command(name="채널설정", help="시참 받을 채널을 설정합니다.")
async def 채널설정(ctx, *, channel_name):
    global TARGET_CHANNEL_ID
    channel = get(ctx.guild.channels, name=channel_name)
    if channel is None:
        await ctx.send(f"'{channel_name}' 채널을 찾을 수 없습니다.")
        return
    TARGET_CHANNEL_ID = channel.id
    with open(CONFIG_FILE, "w") as f:
        json.dump({"TARGET_CHANNEL_ID": TARGET_CHANNEL_ID}, f)
    save_status()
    await ctx.send(f"채널이 <#{TARGET_CHANNEL_ID}> 로 설정되었습니다!")

@bot.command(name="시참시작", help="시참 받기를 시작합니다.")
async def start_count(ctx):
    global counting_active, message_list, reacted_messages
    if TARGET_CHANNEL_ID is None:
        await ctx.send("먼저 이!채널설정으로 채널을 설정해주세요.")
        return
    counting_active = True
    message_list = []
    reacted_messages = []
    save_status()
    await ctx.send(f"<#{TARGET_CHANNEL_ID}> 채널에서 채팅 수 세기를 시작합니다!")

@bot.command(name="시참끝", help="시참 받기를 종료합니다.")
async def stop_count(ctx):
    global counting_active
    counting_active = False
    save_status()
    await ctx.send("채팅 수 세기를 종료했습니다.")

async def channel_check(ctx):
    if TARGET_CHANNEL_ID is None:
        return False
    return ctx.channel.id == TARGET_CHANNEL_ID

@bot.command(name="나바")
async def 나바(ctx):
    if not await channel_check(ctx):
        return
    await ctx.send("루보")

@bot.command(name="돼지")
async def 돼지(ctx):
    if not await channel_check(ctx):
        return
    await ctx.send("토끼")

@bot.command(name="나루")
async def 나루(ctx):
    if not await channel_check(ctx):
        return
    choices = ["바보", "돼지", "토끼"]
    await ctx.send(random.choice(choices))

async def recalc_reactions(deleted_message):
    global message_list, reacted_messages

    message_list[:] = [m for m in message_list if m.id != deleted_message.id]

    new_reacted_ids = {msg.id for i, msg in enumerate(message_list, start=1) if i % 4 == 0}
    old_reacted_ids = {msg.id for msg in reacted_messages}

    for msg in reacted_messages:
        if msg.id not in new_reacted_ids:
            try:
                await msg.clear_reactions()
            except:
                pass

    for msg in message_list:
        if msg.id in new_reacted_ids and msg.id not in old_reacted_ids:
            try:
                await msg.add_reaction("✅")
            except:
                pass

    reacted_messages[:] = [msg for msg in message_list if msg.id in new_reacted_ids]
    save_status()

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    if counting_active and TARGET_CHANNEL_ID and message.channel.id == TARGET_CHANNEL_ID:
        message_list.append(message)
        save_status()
        if len(message_list) % 4 == 0:
            try:
                await message.add_reaction("✅")
                reacted_messages.append(message)
                save_status()
            except:
                pass
    await bot.process_commands(message)

@bot.event
async def on_message_delete(message):
    if counting_active and TARGET_CHANNEL_ID and message.channel.id == TARGET_CHANNEL_ID:
        await recalc_reactions(message)

@bot.command(name="help", help="사용 가능한 명령어를 표시합니다.")
async def help_command(ctx, command_name: str = None):
    if command_name:
        command = bot.get_command(command_name)
        if command and command.help:
            await ctx.send(f"**이!{command.name}** : {command.help}")
        else:
            await ctx.send(f"명령어 `{command_name}` 에 대한 설명이 없습니다.")
        return
    help_text = "**사용 가능한 명령어 목록**\n"
    for cmd in bot.commands:
        if not cmd.hidden and cmd.help:
            help_text += f"- `이!{cmd.name}` : {cmd.help}\n"
    await ctx.send(help_text)

if __name__ == "__main__":
    token = os.getenv("DISCORD_CLOVERTOKEN")
    if not token:
        print("ERROR: No token provided", flush=True)
        sys.exit(1)
    bot.run(token)
