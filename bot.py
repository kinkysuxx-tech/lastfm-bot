import asyncio
import requests
import json
import os
from aiogram import Bot, Dispatcher, types

BOT_TOKEN = "8675764357:AAH6b4IPaa9XCflsLU7RWwvX0Y8T79AhOaw"
LASTFM_API_KEY = "4deef4287c85e0945bb9cb23849fc178"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

DB_FILE = "users.json"

def load_users():
    if not os.path.exists(DB_FILE):
        return {}
    with open(DB_FILE, "r") as f:
        return json.load(f)

def save_users(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f)

users = load_users()

@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    await message.answer("привет 😎 напиши /login")

@dp.message_handler(commands=["login"])
async def login(message: types.Message):
    await message.answer("отправь свой username с last.fm")

@dp.message_handler(lambda message: not message.text.startswith("/"))
async def save_username(message: types.Message):
    users[str(message.from_user.id)] = message.text
    save_users(users)
    await message.answer("сохранил ✅ напиши /recent")
@dp.message_handler(commands=["recent"])
async def recent(message: types.Message):
    user = users.get(str(message.from_user.id))

    if not user:
        await message.answer("сначала /login")
        return

    url = f"http://ws.audioscrobbler.com/2.0/?method=user.getrecenttracks&user={user}&api_key={LASTFM_API_KEY}&format=json"
    r = requests.get(url).json()

    tracks = r["recenttracks"]["track"]

    text = "🎧 последние треки:\n\n"

    for t in tracks[:5]:
        artist = t["artist"]["#text"]
        name = t["name"]
        text += f"{artist} - {name}\n"

    await message.answer(text)
@dp.message_handler(commands=["now"])
async def now(message: types.Message):
    import urllib.parse

    user = users.get(str(message.from_user.id))

    if not user:
        await message.answer("сначала /login")
        return

    url = f"http://ws.audioscrobbler.com/2.0/?method=user.getrecenttracks&user={user}&api_key={LASTFM_API_KEY}&format=json"
    r = requests.get(url).json()

    recent = r.get("recenttracks")

    if not recent or "track" not in recent:
        await message.answer("нет данных 😢")
        return

    tracks = recent["track"]

    if isinstance(tracks, dict):
        tracks = [tracks]

    t = tracks[0]

    artist = t["artist"]["#text"]
    name = t["name"]

    # кодируем для API (ВАЖНО)
    artist_encoded = urllib.parse.quote(artist)
    name_encoded = urllib.parse.quote(name)

    # инфа о треке (твои прослушивания)
    track_info_url = f"http://ws.audioscrobbler.com/2.0/?method=track.getInfo&artist={artist_encoded}&track={name_encoded}&username={user}&api_key={LASTFM_API_KEY}&format=json"
    track_data = requests.get(track_info_url).json()

    user_playcount = track_data.get("track", {}).get("userplaycount", "0")

    # играет ли сейчас
    now_playing = t.get("@attr", {}).get("nowplaying")

    # обложка
    images = t.get("image", [])
    cover = None
    if images:
        cover = images[-1]["#text"]

    # текст
    if now_playing:
        text = f"▶️ сейчас играет:\n{artist} - {name}\n\n🔥 твои прослушивания: {user_playcount}"
    else:
        text = f"⏹ сейчас ничего не играет\nпоследний трек:\n{artist} - {name}\n\n🔥 твои прослушивания: {user_playcount}"

    # отправка
    if cover and cover.strip():
        await message.answer_photo(cover, caption=text)
    else:
        await message.answer(text)
from aiogram import executor

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)