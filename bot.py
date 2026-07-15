import discord
from discord.ext import commands
from datetime import datetime
import asyncio

# ===== КОНФИГУРАЦИЯ =====
TOKEN = "MTUyNjk0MDgwNTc4NzQyMjgzMQ.Gp-Ltj.cwAaDXUcsLOvs6c4Q8PXlyqkvzfmgnbmKJk75Q"  # Замените на реальный токен
LOG_CHANNEL_ID = 1458454605594628229  # ID канала для логов (замените)

# ===== НАСТРОЙКА ИНТЕНТОВ =====
intents = discord.Intents.all()  # Включаем ВСЕ интенты для полного логирования
intents.message_content = True
intents.members = True
intents.voice_states = True
intents.guilds = True
intents.messages = True
intents.reactions = True
intents.moderation = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ===== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ =====
def get_log_channel(guild):
    """Возвращает канал для логов"""
    channel = bot.get_channel(LOG_CHANNEL_ID)
    if channel is None:
        print(f"⚠️ Канал с ID {LOG_CHANNEL_ID} не найден!")
    return channel

async def send_log(guild, message):
    """Отправляет лог в канал"""
    channel = get_log_channel(guild)
    if channel:
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        await channel.send(f"`[{timestamp}]` {message}")

# ===== СОБЫТИЯ =====

# 1. Запуск бота
@bot.event
async def on_ready():
    print(f"✅ Бот {bot.user} запущен и готов к логированию")
    for guild in bot.guilds:
        await send_log(guild, f"🟢 **Бот активирован** на сервере `{guild.name}`")

# 2. СООБЩЕНИЯ
@bot.event
async def on_message(message):
    if message.author.bot:
        return  # Игнорируем ботов
    
    content = message.content[:500] + "..." if len(message.content) > 500 else message.content
    log = (
        f"💬 **Новое сообщение**\n"
        f"Автор: {message.author.mention} (`{message.author}`)\n"
        f"Канал: {message.channel.mention} (`{message.channel.name}`)\n"
        f"Содержание: ```{content}```"
    )
    await send_log(message.guild, log)
    await bot.process_commands(message)

@bot.event
async def on_message_edit(before, after):
    if before.author.bot:
        return
    
    before_content = before.content[:500] + "..." if len(before.content) > 500 else before.content
    after_content = after.content[:500] + "..." if len(after.content) > 500 else after.content
    
    log = (
        f"✏️ **Сообщение изменено**\n"
        f"Автор: {before.author.mention} (`{before.author}`)\n"
        f"Канал: {before.channel.mention}\n"
        f"Было: ```{before_content}```\n"
        f"Стало: ```{after_content}```"
    )
    await send_log(before.guild, log)

@bot.event
async def on_message_delete(message):
    if message.author.bot:
        return
    
    content = message.content[:500] + "..." if len(message.content) > 500 else message.content
    log = (
        f"🗑️ **Сообщение удалено**\n"
        f"Автор: {message.author.mention} (`{message.author}`)\n"
        f"Канал: {message.channel.mention}\n"
        f"Содержание: ```{content}```"
    )
    await send_log(message.guild, log)

@bot.event
async def on_bulk_message_delete(messages):
    if not messages:
        return
    guild = messages[0].guild
    channel = messages[0].channel
    count = len(messages)
    log = f"🧹 **Массовое удаление** {count} сообщений в канале {channel.mention}"
    await send_log(guild, log)

# 3. ГОЛОСОВЫЕ КАНАЛЫ
@bot.event
async def on_voice_state_update(member, before, after):
    guild = member.guild
    
    # Вход в канал
    if before.channel is None and after.channel is not None:
        log = (
            f"🔊 **Вход в голосовой канал**\n"
            f"Участник: {member.mention} (`{member}`)\n"
            f"Канал: {after.channel.mention} (`{after.channel.name}`)"
        )
        await send_log(guild, log)
    
    # Выход из канала
    elif before.channel is not None and after.channel is None:
        log = (
            f"🔇 **Выход из голосового канала**\n"
            f"Участник: {member.mention} (`{member}`)\n"
            f"Был в: {before.channel.mention} (`{before.channel.name}`)"
        )
        await send_log(guild, log)
    
    # Перемещение между каналами
    elif before.channel != after.channel and before.channel is not None and after.channel is not None:
        log = (
            f"🔄 **Перемещение по голосовым каналам**\n"
            f"Участник: {member.mention} (`{member}`)\n"
            f"Из: {before.channel.mention} (`{before.channel.name}`)\n"
            f"В: {after.channel.mention} (`{after.channel.name}`)"
        )
        await send_log(guild, log)
    
    # Изменение состояния (заглушен/не заглушен и т.д.)
    elif before.self_deaf != after.self_deaf:
        status = "заглушил" if after.self_deaf else "включил звук"
        log = f"🔇 {member.mention} {status} себя в голосовом канале"
        await send_log(guild, log)
    
    elif before.self_mute != after.self_mute:
        status = "выключил" if after.self_mute else "включил"
        log = f"🎙️ {member.mention} {status} микрофон в голосовом канале"
        await send_log(guild, log)

# 4. УЧАСТНИКИ
@bot.event
async def on_member_join(member):
    log = (
        f"🟢 **Новый участник на сервере**\n"
        f"Участник: {member.mention} (`{member}`)\n"
        f"Аккаунт создан: {member.created_at.strftime('%Y-%m-%d %H:%M:%S')}"
    )
    await send_log(member.guild, log)

@bot.event
async def on_member_remove(member):
    log = (
        f"🔴 **Участник покинул сервер**\n"
        f"Участник: `{member}` (ID: {member.id})"
    )
    await send_log(member.guild, log)

@bot.event
async def on_member_update(before, after):
    # Смена никнейма
    if before.nick != after.nick:
        old = before.nick or before.name
        new = after.nick or after.name
        log = f"📝 **Смена никнейма**\nУчастник: {after.mention}\nБыл: `{old}`\nСтал: `{new}`"
        await send_log(after.guild, log)
    
    # Смена ролей
    if before.roles != after.roles:
        added = set(after.roles) - set(before.roles)
        removed = set(before.roles) - set(after.roles)
        
        if added:
            roles = ", ".join([r.mention for r in added])
            log = f"➕ **Добавлены роли** для {after.mention}\nРоли: {roles}"
            await send_log(after.guild, log)
        
        if removed:
            roles = ", ".join([r.mention for r in removed])
            log = f"➖ **Удалены роли** у {after.mention}\nРоли: {roles}"
            await send_log(after.guild, log)

# 5. РЕАКЦИИ
@bot.event
async def on_reaction_add(reaction, user):
    if user.bot:
        return
    
    log = (
        f"➕ **Добавлена реакция**\n"
        f"Пользователь: {user.mention}\n"
        f"Сообщение: [ссылка]({reaction.message.jump_url})\n"
        f"Реакция: {reaction.emoji}"
    )
    await send_log(reaction.message.guild, log)

@bot.event
async def on_reaction_remove(reaction, user):
    if user.bot:
        return
    
    log = (
        f"➖ **Удалена реакция**\n"
        f"Пользователь: {user.mention}\n"
        f"Сообщение: [ссылка]({reaction.message.jump_url})\n"
        f"Реакция: {reaction.emoji}"
    )
    await send_log(reaction.message.guild, log)

# 6. ИЗМЕНЕНИЯ В КАНАЛАХ
@bot.event
async def on_guild_channel_create(channel):
    log = f"🆕 **Создан канал**\n{channel.mention} (`{channel.name}`) типа `{channel.type}`"
    await send_log(channel.guild, log)

@bot.event
async def on_guild_channel_delete(channel):
    log = f"🗑️ **Удалён канал**\n`{channel.name}` (ID: {channel.id}) типа `{channel.type}`"
    await send_log(channel.guild, log)

@bot.event
async def on_guild_channel_update(before, after):
    if before.name != after.name:
        log = f"✏️ **Канал переименован**\nБыло: `{before.name}`\nСтало: {after.mention} (`{after.name}`)"
        await send_log(after.guild, log)

# 7. МОДЕРАЦИЯ (баны/кики)
@bot.event
async def on_member_ban(guild, user):
    log = f"⛔ **Бан участника**\nУчастник: `{user}` (ID: {user.id})\nСервер: {guild.name}"
    await send_log(guild, log)

@bot.event
async def on_member_unban(guild, user):
    log = f"✅ **Разбан участника**\nУчастник: `{user}` (ID: {user.id})\nСервер: {guild.name}"
    await send_log(guild, log)

# 8. КОМАНДА ДЛЯ ПРОВЕРКИ РАБОТЫ
@bot.command(name="test_log")
async def test_log(ctx):
    """Тестовая команда для проверки логирования"""
    await send_log(ctx.guild, "🧪 **Тестовый лог** — бот работает корректно!")

@bot.command(name="log_channel")
@commands.has_permissions(administrator=True)
async def set_log_channel(ctx, channel_id: int):
    """Установить канал для логов (админ)"""
    global LOG_CHANNEL_ID
    channel = bot.get_channel(channel_id)
    if channel is None:
        await ctx.send("❌ Канал с таким ID не найден!")
        return
    LOG_CHANNEL_ID = channel_id
    await ctx.send(f"✅ Канал для логов установлен: {channel.mention}")

# ===== ЗАПУСК =====
bot.run(TOKEN)
