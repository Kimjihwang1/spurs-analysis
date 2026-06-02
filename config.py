import os
from dotenv import load_dotenv

load_dotenv()

API_KEY  = os.getenv("API_KEY")
BASE_URL = "https://v3.football.api-sports.io"
HEADERS  = {"x-apisports-key": API_KEY}

LEAGUE_ID = 39    # 프리미어리그
SEASON    = 2024  # 24/25 시즌
SPURS_ID  = 47    # 토트넘 팀 ID``