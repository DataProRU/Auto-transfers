from os import getenv
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = getenv("BOT_TOKEN")
ADMIN_GROUP_ID = getenv("ADMIN_GROUP_ID")

if not all([BOT_TOKEN, ADMIN_GROUP_ID]):
    raise ValueError("Необходимо установить BOT_TOKEN и ADMIN_GROUP_ID в файле .env") 