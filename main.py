import discord
import asyncio
from discord.ext import commands, tasks
from discord import app_commands
import datetime
import time
import random
import string
import os
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

print(f"Токен загружен: {'Да' if TOKEN else 'Нет'}")
print(f"Длина токена: {len(TOKEN) if TOKEN else 0}")

if not TOKEN:
    print("❌ ОШИБКА: Токен не найден в .env файле!")
    exit(1)
    print("🔧 1. Начало загрузки...")
load_dotenv()
print("🔧 2. .env загружен")

TOKEN = os.getenv('DISCORD_TOKEN')
print(f"🔧 3. Токен получен, длина: {len(TOKEN)}")

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.voice_states = True
print("🔧 4. Интенты установлены")

bot = discord.Bot(intents=intents)
print("🔧 5. Бот создан")

@bot.event
async def on_ready():
    print(f"✅ Бот {bot.user} запущен!")

@bot.event
async def on_connect():
    print("🔧 6. Подключение к Discord установлено")

@bot.event
async def on_disconnect():
    print("🔧 7. Отключение от Discord")

print("🔧 8. Запускаем bot.run()...")
try:
    bot.run(TOKEN)
except Exception as e:
    print(f"❌ Ошибка: {e}")
print("🔧 9. Код после bot.run()")

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix='!', intents=intents)

# Хранилище
temp_channels = {}
room_bans = {}
private_rooms = {}
password_sessions = {}

# 🔧 ПРОВЕРКА КАТЕГОРИЙ ПРИ ЗАПУСКЕ
async def check_categories():
    """Проверяет доступность всех категорий при запуске бота"""
    print("🔍 Проверка категорий...")
    
    categories_to_check = [
        1437877099649306757,  # DUO
        1439160170377904199,  # SQUAD  
        1438924322356859153,  # GAUNTLET
        1439571047082098892,  # PRIVATE
        1439146881333723267   # FULL
    ]
    
    for category_id in categories_to_check:
        category = bot.get_channel(category_id)
        if category:
            print(f"✅ Категория найдена: {category.name} (ID: {category_id})")
        else:
            print(f"❌ Категория не найдена: {category_id}")

# Конфиг комнат - УБЕДИТЕСЬ ЧТО ID КАТЕГОРИЙ ПРАВИЛЬНЫЕ!
ROOM_CONFIGS = {
    1439156275320455188: {
        "user_limit": 2,
        "category_id": 1437877099649306757,
        "emoji": "👥",
        "room_name": "DUO", 
        "display_name": "DUO",
        "target_category": 1437877099649306757  # Категория для DUO комнат
    },
    1439160527854239756: {
        "user_limit": 4,
        "category_id": 1439160170377904199,
        "emoji": "⚡️",
        "room_name": "SQUAD",
        "display_name": "SQUAD",
        "target_category": 1439160170377904199  # Категория для SQUAD комнат
    },
    1439157120283971654: {
        "user_limit": 4,
        "category_id": 1438924322356859153,
        "emoji": "💣",
        "room_name": "GAUNTLET",
        "display_name": "GAUNTLET",
        "target_category": 1438924322356859153  # Категория для GAUNTLET комнат
    },
    1439319224634835059: {
        "user_limit": 10,
        "category_id": 1439319223162769654,
        "emoji": "🔒",
        "room_name": "PRIVATE", 
        "display_name": "PRIVATE",
        "target_category": 1439571047082098892  # Категория для PRIVATE комнат
    }
}

FULL_ROOMS_CATEGORY_ID = 1439146881333723267
PRIVATE_ROOMS_CATEGORY_ID = 1439571047082098892

# 🔧 ФУНКЦИЯ ДЛЯ УДАЛЕНИЯ КОМНАТЫ
async def delete_temp_channel(channel_id):
    """Удаляет временную комнату и очищает все связанные данные"""
    try:
        channel = bot.get_channel(channel_id)
        if channel:
            print(f"🗑️ Удаляем комнату: {channel.name} (ID: {channel.id})")
            await channel.delete()
            print(f"✅ Комната успешно удалена: {channel.name}")
        else:
            print(f"ℹ️ Канал {channel_id} уже удален")
        
        # Очищаем все данные
        if channel_id in temp_channels:
            del temp_channels[channel_id]
        if channel_id in room_bans:
            del room_bans[channel_id]
        if channel_id in private_rooms:
            del private_rooms[channel_id]
            
    except discord.NotFound:
        print(f"ℹ️ Канал {channel_id} уже удален")
    except Exception as e:
        print(f"❌ Ошибка при удалении комнаты {channel_id}: {e}")

# 🔧 ФУНКЦИЯ ДЛЯ ПРОВЕРКИ ПУСТЫХ КОМНАТ
async def check_and_delete_empty_rooms():
    """Проверяет и удаляет все пустые временные комнаты"""
    rooms_to_delete = []
    
    for channel_id, temp_data in list(temp_channels.items()):
        try:
            channel = bot.get_channel(channel_id)
            if not channel:
                print(f"❌ Канал {channel_id} не найден, удаляем из памяти")
                rooms_to_delete.append(channel_id)
                continue
                
            member_count = len(channel.members)
            print(f"🔍 Проверка комнаты: {channel.name} | Участников: {member_count}")
            
            if member_count == 0:
                print(f"🗑️ Найден пустой канал для удаления: {channel.name}")
                rooms_to_delete.append(channel_id)
                
        except Exception as e:
            print(f"❌ Ошибка при проверке канала {channel_id}: {e}")
            rooms_to_delete.append(channel_id)
    
    # Удаляем найденные пустые комнаты
    for channel_id in rooms_to_delete:
        await delete_temp_channel(channel_id)

# 🔧 ФОНОВАЯ ЗАДАЧА ДЛЯ ОЧИСТКИ КОМНАТ
@tasks.loop(minutes=1)
async def cleanup_empty_rooms():
    """Фоновая задача для очистки пустых комнат"""
    print("🔄 Запуск фоновой очистки комнат...")
    await check_and_delete_empty_rooms()

class PasswordView(discord.ui.View):
    def __init__(self, user_id, channel_id, correct_password):
        super().__init__(timeout=120)
        self.user_id = user_id
        self.channel_id = channel_id
        self.correct_password = correct_password
        self.entered_password = ""
        
    @discord.ui.button(label="1", style=discord.ButtonStyle.gray, row=0)
    async def btn_1(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.add_digit(interaction, "1")
        
    @discord.ui.button(label="2", style=discord.ButtonStyle.gray, row=0)
    async def btn_2(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.add_digit(interaction, "2")
        
    @discord.ui.button(label="3", style=discord.ButtonStyle.gray, row=0)
    async def btn_3(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.add_digit(interaction, "3")
        
    @discord.ui.button(label="4", style=discord.ButtonStyle.gray, row=1)
    async def btn_4(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.add_digit(interaction, "4")
        
    @discord.ui.button(label="5", style=discord.ButtonStyle.gray, row=1)
    async def btn_5(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.add_digit(interaction, "5")
        
    @discord.ui.button(label="6", style=discord.ButtonStyle.gray, row=1)
    async def btn_6(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.add_digit(interaction, "6")
        
    @discord.ui.button(label="7", style=discord.ButtonStyle.gray, row=2)
    async def btn_7(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.add_digit(interaction, "7")
        
    @discord.ui.button(label="8", style=discord.ButtonStyle.gray, row=2)
    async def btn_8(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.add_digit(interaction, "8")
        
    @discord.ui.button(label="9", style=discord.ButtonStyle.gray, row=2)
    async def btn_9(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.add_digit(interaction, "9")
        
    @discord.ui.button(label="0", style=discord.ButtonStyle.gray, row=3)
    async def btn_0(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.add_digit(interaction, "0")
        
    @discord.ui.button(label="⌫", style=discord.ButtonStyle.red, row=3)
    async def btn_backspace(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.entered_password = self.entered_password[:-1]
        await self.update_embed(interaction)
        
    @discord.ui.button(label="✅ Проверить", style=discord.ButtonStyle.green, row=3)
    async def btn_submit(self, interaction: discord.Interaction, button: discord.ui.Button):
        if len(self.entered_password) != 4:
            await interaction.response.send_message("❌ Пароль должен содержать 4 цифры!", ephemeral=True)
            return
            
        if self.entered_password == self.correct_password:
            channel = bot.get_channel(self.channel_id)
            if channel and channel.id in private_rooms:
                room_data = private_rooms[channel.id]
                if "members" not in room_data:
                    room_data["members"] = []
                if self.user_id not in room_data["members"]:
                    room_data["members"].append(self.user_id)
                
                if self.user_id in password_sessions:
                    del password_sessions[self.user_id]
                
                await interaction.response.edit_message(
                    content="✅ Пароль верный! Теперь вы можете зайти в приватную комнату.",
                    view=None,
                    embed=None
                )
            else:
                await interaction.response.edit_message(
                    content="❌ Комната больше не доступна.",
                    view=None,
                    embed=None
                )
        else:
            if self.user_id in password_sessions:
                password_sessions[self.user_id]["attempts"] += 1
                attempts = password_sessions[self.user_id]["attempts"]
                
                if attempts >= 3:
                    await interaction.response.edit_message(
                        content="❌ Слишком много неверных попыток. Доступ заблокирован.",
                        view=None,
                        embed=None
                    )
                    del password_sessions[self.user_id]
                else:
                    self.entered_password = ""
                    await interaction.response.edit_message(
                        content=f"❌ Неверный пароль! Попыток осталось: {3 - attempts}",
                        embed=self.create_embed()
                    )
    
    async def add_digit(self, interaction: discord.Interaction, digit: str):
        if len(self.entered_password) < 4:
            self.entered_password += digit
            await self.update_embed(interaction)
    
    async def update_embed(self, interaction: discord.Interaction):
        await interaction.response.edit_message(embed=self.create_embed())
    
    def create_embed(self):
        embed = discord.Embed(
            title="🔒 Введите пароль",
            description=f"Пароль: `{'*' * len(self.entered_password)}{'_' * (4 - len(self.entered_password))}`",
            color=0xff9900
        )
        embed.set_footer(text="Нажмите цифры чтобы ввести пароль")
        return embed

@bot.event
async def on_ready():
    print(f'✅ Бот {bot.user} запущен!')
    # Проверяем категории при запуске
    await check_categories()
    # Запускаем фоновую задачу очистки
    cleanup_empty_rooms.start()
    print('✅ Фоновая задача очистки комнат запущена!')

# 🔧 ГЕНЕРАЦИЯ ПАРОЛЯ
def generate_password():
    return ''.join(random.choices(string.digits, k=4))

# 🔧 ФУНКЦИЯ ДЛЯ ПОЛУЧЕНИЯ КАТЕГОРИИ С РЕЗЕРВНЫМ ВАРИАНТОМ
async def get_category_with_fallback(category_id, fallback_category_id=None):
    """Получает категорию, если не найдена - использует запасную или создает в корне"""
    category = bot.get_channel(category_id)
    if category:
        return category
    
    if fallback_category_id:
        fallback_category = bot.get_channel(fallback_category_id)
        if fallback_category:
            print(f"⚠️ Используем запасную категорию: {fallback_category.name}")
            return fallback_category
    
    # Если категории не найдены, создаем в корне сервера
    guild = bot.guilds[0] if bot.guilds else None
    if guild:
        print(f"⚠️ Категория {category_id} не найдена, создаем комнаты в корне сервера")
        return None  # None означает создание в корне
    
    return None

# 🔧 СИСТЕМА ЛИЧНЫХ КОМНАТ
@bot.event
async def on_voice_state_update(member, before, after):
    try:
        # 🔧 ПРОВЕРКА ПУСТЫХ КОМНАТ ПРИ ВЫХОДЕ
        if before and before.channel and before.channel.id in temp_channels:
            channel = before.channel
            print(f"🔍 Пользователь {member.display_name} вышел из {channel.name} | Участников: {len(channel.members)}")
            
            # Немедленная проверка на пустоту
            if len(channel.members) == 0:
                print(f"🗑️ Комната опустела, удаляем: {channel.name}")
                await delete_temp_channel(channel.id)
            else:
                # Для обычных комнат проверяем перемещение из FULL категории
                if channel.id not in private_rooms:
                    temp_data = temp_channels[channel.id]
                    current_members = len(channel.members)
                    user_limit = temp_data["config"]["user_limit"]
                    
                    if channel.category_id == FULL_ROOMS_CATEGORY_ID and current_members < user_limit:
                        original_category = await get_category_with_fallback(temp_data["original_category"])
                        if original_category:
                            try:
                                await channel.edit(category=original_category)
                                print(f"✅ Возвращена из FULL: {channel.name}")
                            except Exception as e:
                                print(f"❌ Ошибка возврата из FULL: {e}")
        
        # 🔧 СОЗДАНИЕ НОВЫХ КОМНАТ
        if after and after.channel and after.channel.id in ROOM_CONFIGS:
            config = ROOM_CONFIGS[after.channel.id]
            target_category_id = config["target_category"]
            
            # Получаем категорию с запасным вариантом
            target_category = await get_category_with_fallback(target_category_id, config["category_id"])
            
            if not target_category:
                print(f"⚠️ Категория {target_category_id} не найдена, создаем в корне сервера")
            
            # Создаем комнату
            if after.channel.id == 1439319224634835059:  # ПРИВАТНЫЕ КОМНАТЫ
                password = generate_password()
                channel_name = f"🔒 {member.display_name}'s Room"
                
                if target_category:
                    temp_channel = await target_category.create_voice_channel(
                        name=channel_name,
                        user_limit=config["user_limit"]
                    )
                else:
                    # Создаем в корне сервера
                    temp_channel = await member.guild.create_voice_channel(
                        name=channel_name,
                        user_limit=config["user_limit"]
                    )
                
                await member.move_to(temp_channel)
                
                temp_channels[temp_channel.id] = {
                    "owner": member.id,
                    "created_at": time.time(),
                    "config": config,
                    "original_category": target_category.id if target_category else None
                }
                
                private_rooms[temp_channel.id] = {
                    "password": password,
                    "owner": member.id,
                    "members": []
                }
                
                print(f"🔒 Приватная комната создана: {temp_channel.name} | Пароль: {password}")
                
                # Отправляем пароль владельцу
                try:
                    embed = discord.Embed(
                        title="🔒 Ваша приватная комната создана!",
                        description=f"**Пароль для входа:** `{password}`\n\nДелитесь этим паролем с друзьями, чтобы они могли присоединиться к вашей комнате.",
                        color=0x00ff00
                    )
                    await member.send(embed=embed)
                    print(f"✅ Пароль отправлен владельцу: {password}")
                except Exception as e:
                    print(f"❌ Не удалось отправить пароль в ЛС: {e}")
                
            else:  # ОБЫЧНЫЕ КОМНАТЫ
                channel_name = f"{config['emoji']} {config['display_name']} | {member.display_name}"
                
                if target_category:
                    temp_channel = await target_category.create_voice_channel(
                        name=channel_name,
                        user_limit=config["user_limit"]
                    )
                else:
                    # Создаем в корне сервера
                    temp_channel = await member.guild.create_voice_channel(
                        name=channel_name,
                        user_limit=config["user_limit"]
                    )
                
                await member.move_to(temp_channel)
                
                temp_channels[temp_channel.id] = {
                    "owner": member.id,
                    "created_at": time.time(),
                    "config": config,
                    "original_category": target_category.id if target_category else None
                }
                print(f"✅ Комната создана: {temp_channel.name}")
        
        # 🔒 ПРОВЕРКА ДОСТУПА К ПРИВАТНЫМ КОМНАТАМ
        if after and after.channel and after.channel.id in private_rooms:
            channel = after.channel
            room_data = private_rooms[channel.id]
            
            # Владелец может заходить без пароля
            if member.id == room_data["owner"]:
                return
                
            # Если пользователь уже в списке участников - разрешаем вход
            if "members" in room_data and member.id in room_data["members"]:
                return
            
            # ЕСЛИ НЕТ ДОСТУПА - ВЫКИДЫВАЕМ И ПРЕДЛАГАЕМ ВВЕСТИ ПАРОЛЬ
            await member.move_to(None)
            print(f"🚫 Пользователь {member.display_name} не имеет доступа к приватной комнате")
            
            # Создаем сессию для ввода пароля
            password_sessions[member.id] = {
                "channel_id": channel.id,
                "password": room_data["password"],
                "attempts": 0
            }
            
            # ОТПРАВЛЯЕМ ПАНЕЛЬ ПАРОЛЯ
            try:
                embed = discord.Embed(
                    title="🔒 Приватная комната",
                    description=f"Комната **{channel.name}** защищена паролем.\n\nИспользуйте кнопки ниже чтобы ввести пароль:",
                    color=0xff9900
                )
                
                view = PasswordView(member.id, channel.id, room_data["password"])
                await member.send(embed=embed, view=view)
                print(f"📨 Панель пароля отправлена пользователю {member.display_name}")
                
            except discord.Forbidden:
                print(f"❌ Не удалось отправить ЛС пользователю {member.display_name} (запрещено)")
            except Exception as e:
                print(f"❌ Ошибка при отправке панели пароля: {e}")
        
        # 🔄 ПРОВЕРКА ПЕРЕМЕЩЕНИЯ В FULL КАТЕГОРИЮ ДЛЯ ОБЫЧНЫХ КОМНАТ
        if after and after.channel and after.channel.id in temp_channels and after.channel.id not in private_rooms:
            channel = after.channel
            temp_data = temp_channels[channel.id]
            current_members = len(channel.members)
            user_limit = temp_data["config"]["user_limit"]
            
            if current_members >= user_limit and channel.category_id != FULL_ROOMS_CATEGORY_ID:
                full_category = bot.get_channel(FULL_ROOMS_CATEGORY_ID)
                if full_category:
                    try:
                        await channel.edit(category=full_category)
                        print(f"🚨 Комната перемещена в FULL: {channel.name}")
                    except Exception as e:
                        print(f"❌ Ошибка перемещения в FULL: {e}")
    
    except Exception as e:
        print(f"❌ Критическая ошибка в on_voice_state_update: {e}")

# ... (остальной код команд остается без изменений)

# Контекстное меню для выгона из комнаты
@bot.tree.context_menu(name="Выгнать из комнаты")
async def kick_user(interaction: discord.Interaction, member: discord.Member):
    guild = interaction.guild
    if not guild:
        await interaction.response.send_message("❌ Ошибка сервера", ephemeral=True)
        return
    
    target_in_voice = None
    for voice_channel in guild.voice_channels:
        if member in voice_channel.members:
            target_in_voice = voice_channel
            break
    
    if target_in_voice and target_in_voice.id in temp_channels:
        temp_data = temp_channels[target_in_voice.id]
        
        if temp_data["owner"] == interaction.user.id:
            await member.move_to(None)
            
            if target_in_voice.id not in room_bans:
                room_bans[target_in_voice.id] = []
            
            if member.id not in room_bans[target_in_voice.id]:
                room_bans[target_in_voice.id].append(member.id)
            
            if target_in_voice.id in private_rooms:
                room_data = private_rooms[target_in_voice.id]
                if "members" in room_data and member.id in room_data["members"]:
                    room_data["members"].remove(member.id)
            
            # Удаляем сессию пароля если есть
            if member.id in password_sessions:
                del password_sessions[member.id]
            
            try:
                text_channel = interaction.channel
                if isinstance(text_channel, discord.TextChannel):
                    await text_channel.send(f"🚫 {member.mention} был исключен из комнаты {target_in_voice.name}!")
            except:
                pass
            
            await interaction.response.send_message(
                f"✅ {member.mention} выгнан из комнаты!\n⏰ Забанен в этой комнате",
                ephemeral=True
            )
            print(f"🚫 {member.display_name} забанен в комнате {target_in_voice.name}")
            
            try:
                await member.send(f"🚫 Вы были исключены из комнаты '{target_in_voice.name}'!")
            except:
                pass
                
        else:
            await interaction.response.send_message("❌ Вы не владелец этой комнаты!", ephemeral=True)
    else:
        await interaction.response.send_message("❌ Пользователь не в голосовой комнате!", ephemeral=True)

# 🔧 КОМАНДА ДЛЯ ПОЛУЧЕНИЯ ПАРОЛЯ
@bot.tree.command(name="get_password", description="Получить пароль от вашей приватной комнаты")
async def get_password(interaction: discord.Interaction):
    user_private_room = None
    for channel_id, room_data in private_rooms.items():
        if room_data["owner"] == interaction.user.id:
            user_private_room = channel_id
            break
    
    if user_private_room:
        password = private_rooms[user_private_room]["password"]
        await interaction.response.send_message(
            f"🔒 Пароль от вашей комнаты: `{password}`\nПоделитесь им с друзьями!",
            ephemeral=True
        )
    else:
        await interaction.response.send_message("❌ У вас нет активной приватной комнаты!", ephemeral=True)

# 🔧 КОМАНДА ДЛЯ СБРОСА ПАРОЛЯ
@bot.tree.command(name="reset_password", description="Сгенерировать новый пароль для приватной комнаты")
async def reset_password(interaction: discord.Interaction):
    user_private_room = None
    for channel_id, room_data in private_rooms.items():
        if room_data["owner"] == interaction.user.id:
            user_private_room = channel_id
            break
    
    if user_private_room:
        new_password = generate_password()
        private_rooms[user_private_room]["password"] = new_password
        
        await interaction.response.send_message(
            f"🔒 Новый пароль от вашей комнаты: `{new_password}`",
            ephemeral=True
        )
    else:
        await interaction.response.send_message("❌ У вас нет активной приватной комнаты!", ephemeral=True)

TOKEN = os.getenv('DISCORD_TOKEN')

bot.run(TOKEN)

