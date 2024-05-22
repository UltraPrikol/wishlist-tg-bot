import logging
import asyncio
from aiogram import Bot, Dispatcher
from handlers import friends, wishlist
from dotenv import dotenv_values


config = dotenv_values('.env')
BOT_TOKEN = config['BOT_TOKEN']


async def main():
    bot = Bot(token=BOT_TOKEN, parse_mode="HTML")
    logging.basicConfig(level=logging.INFO)
    dp = Dispatcher()
    dp.include_routers(wishlist.router, friends.router)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
