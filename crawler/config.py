import os
from dotenv import load_dotenv

load_dotenv()

def get_target_url():
    return os.getenv("CRAWL_TARGET_URL") 