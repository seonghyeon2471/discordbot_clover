import discord
from discord.ext import commands
from discord.utils import get
import json
import os
import random  # 랜덤 모듈

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="이!", intents=intents, help_command=None)

CONFIG_FILE = "naru_config.json"  # 내용 저장할 json파일
TARGET_CHANNEL_ID = None  # 채널 ID
counting_active = False  # 채팅 수 세기 시작/종료

message_list = []
reacted_messages = []  # 4번째 메시지 추적

# ----------------------
# 기존 설정 불러오기
# ----------------------
if os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE, "r") as f:
        data = json.load(f)
        TARGET_CHANNEL_ID = data.get("TARGET_CHANNEL_ID")

# ----------------------
# 봇 준비 완료
# ----------------------
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

# ----------------------
# 채널 설정 명령어
# ----------------------
@bot.command(name="채널설정", help="시참 받을 채널을 설정합니다.")
async def 채널설정(ctx, *, channel_name):
    global TARGET_CHANNEL_ID
    channel = get(ctx.guild.channels, name=channel_name)
    
    if channel is None:
        await ctx.send(f"'{channel_name}' 채널을 찾을 수 없습니다.")
        return

    TARGET_CHANNEL_ID = channel.id
    # 새 파일에 저장
    with open(CONFIG_FILE, "w") as f:
        json.dump({"TARGET_CHANNEL_ID": TARGET_CHANNEL_ID}, f)

    await ctx.send(f"채널이 <#{TARGET_CHANNEL_ID}> 로 설정되었습니다!")

# ----------------------
# 시참 시작/종료
# ----------------------
@bot.command(name="시참시작", help="시참 받기를 시작합니다.")
async def start_count(ctx):
    global counting_active, message_list, reacted_messages
    if TARGET_CHANNEL_ID is None:
        await ctx.send("먼저 이!채널설정으로 채널을 설정해주세요.")
        return

    counting_active = True
    message_list = []
    reacted_messages = []
    await ctx.send(f"<#{TARGET_CHANNEL_ID}> 채널에서 채팅 수 세기를 시작합니다!")

@bot.command(name="시참끝", help="시참 받기를 종료합니다.")
async def stop_count(ctx):
    global counting_active
    counting_active = False
    await ctx.send("채팅 수 세기를 종료했습니다.")

# ----------------------
# 공통 채널 체크 (지정 채널이 아니면 아무 반응 없음)
# ----------------------
async def channel_check(ctx):
    if TARGET_CHANNEL_ID is None:
        return False
    if ctx.channel.id != TARGET_CHANNEL_ID:
        return False
    return True

# ----------------------
# 명령어 (특정 채널 제한)
# ----------------------
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
    choices = ["바보", "돼지", "토끼"]  # 랜덤 선택지
    selected = random.choice(choices)
    await ctx.send(f"{selected}")

# ----------------------
# 메시지 이벤트 처리
# ----------------------
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if counting_active and TARGET_CHANNEL_ID and message.channel.id == TARGET_CHANNEL_ID:
        message_list.append(message)

        # 4번째마다 리액션 추가
        if len(message_list) % 4 == 0:
            await message.add_reaction("✅")
            reacted_messages.append(message)
        else:
            # 4번째가 아닌데 봇이 달았던 ✅ 리액션 제거
            try:
                for reaction in message.reactions:
                    if str(reaction.emoji) == "✅":
                        users = await reaction.users().flatten()
                        if bot.user in users:
                            await reaction.remove(bot.user)
            except:
                pass

    await bot.process_commands(message)

@bot.event
async def on_message_delete(message):
    if TARGET_CHANNEL_ID and message.channel.id == TARGET_CHANNEL_ID:
        if message in message_list:
            message_list.remove(message)

        if message in reacted_messages:
            try:
                await message.clear_reactions()
            except:
                pass
            reacted_messages.remove(message)

# ----------------------
# 자동 help 명령어
# ----------------------
@bot.command(name="help", help="사용 가능한 명령어를 표시합니다.")
async def help_command(ctx, command_name: str = None):
    """자동 help 명령어. 명령어 이름 입력 시 상세 설명, 없으면 전체 목록"""
    
    if command_name:
        # 특정 명령어 도움말
        command = bot.get_command(command_name)
        if command and command.help:
            await ctx.send(f"**이!{command.name}** : {command.help}")
        else:
            await ctx.send(f"명령어 `{command_name}` 에 대한 설명이 없습니다.")
        return

    # 전체 명령어 목록 (help 속성이 있는 것만)
    help_text = "**사용 가능한 명령어 목록**\n"
    for cmd in bot.commands:
        if not cmd.hidden and cmd.help:  # help 속성이 있는 것만 표시
            help_text += f"- `이!{cmd.name}` : {cmd.help}\n"

    await ctx.send(help_text)

# ----------------------
# 봇 실행
# ----------------------
import os
bot.run(os.environ["DISCORD_TOKEN"])
