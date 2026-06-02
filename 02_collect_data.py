import requests
import json
import os
import time
from config import BASE_URL, HEADERS, LEAGUE_ID, SEASON, SPURS_ID
os.chdir(os.path.dirname(os.path.abspath(__file__)))

def api_get(endpoint, params={}):
    url = f"{BASE_URL}/{endpoint}"
    try:
        response = requests.get(url, headers=HEADERS, params=params)
        remaining = response.headers.get("x-ratelimit-requests-remaining", "?")
        print(f"✅ {endpoint} | 남은 콜: {remaining}")
        data = response.json()
        if data.get("errors"):
            print(f"  ⚠️ API 에러: {data['errors']}")
            return None
        time.sleep(10)  # 0.5 → 1초로 늘리기
        return data
    except Exception as e:
        print(f"❌ 요청 실패: {e}")
        return None

def save_data(filename, data):
    os.makedirs("data", exist_ok=True)
    with open(f"data/{filename}", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"저장 완료: data/{filename}")


# 1. 토트넘 경기 목록 (38경기)
def get_spurs_fixtures():
    return api_get("fixtures", {
        "team": SPURS_ID,
        "league": LEAGUE_ID,
        "season": SEASON
    })


# 2. 토트넘 시즌 팀 통계
def get_spurs_stats():
    return api_get("teams/statistics", {
        "team": SPURS_ID,
        "league": LEAGUE_ID,
        "season": SEASON
    })


# 3. 토트넘 부상자 목록
def get_spurs_injuries():
    return api_get("injuries", {
        "team": SPURS_ID,
        "league": LEAGUE_ID,
        "season": SEASON
    })


# 4. 리그 전체 20개 팀 통계 (비교용)
PL_TEAMS = {
    42: "Arsenal",        33: "Manchester United", 40: "Liverpool",
    50: "Manchester City", 49: "Chelsea",          47: "Tottenham",
    66: "Aston Villa",    34: "Newcastle",         51: "Brighton",
    52: "Crystal Palace", 55: "Brentford",         48: "West Ham",
    45: "Everton",        35: "Bournemouth",       36: "Fulham",
    44: "Nottingham Forest", 39: "Wolves",         46: "Leicester",
    1359: "Burnley",      41: "Southampton"
}

def get_all_teams_stats():
    all_stats = {}
    for team_id, team_name in PL_TEAMS.items():
        print(f"수집 중: {team_name}...")
        data = api_get("teams/statistics", {
            "team": team_id,
            "league": LEAGUE_ID,
            "season": SEASON
        })
        if data and data.get("response"):
            all_stats[team_name] = data["response"]
    return all_stats

# 5. 토트넘 38경기 개별 statistics (슈팅, 유효슈팅, 점유율)
def get_spurs_match_stats():
    # fixture_id 목록 불러오기
    with open("data/spurs_fixtures.json", "r", encoding="utf-8") as f:
        fixtures = json.load(f)
    
    fixture_ids = [match["fixture"]["id"] for match in fixtures["response"]]
    all_match_stats = {}

    for fid in fixture_ids:
        print(f"수집 중: fixture {fid}...")
        data = api_get("fixtures/statistics", {
            "fixture": fid,
            "team": SPURS_ID
        })
        if data and data.get("response"):
            all_match_stats[fid] = data["response"]
    
    return all_match_stats

# 실행
if __name__ == "__main__":
    print("=== 데이터 수집 시작 ===\n")

    fixtures = get_spurs_fixtures()
    save_data("spurs_fixtures.json", fixtures)

    stats = get_spurs_stats()
    save_data("spurs_stats.json", stats)

    injuries = get_spurs_injuries()
    save_data("spurs_injuries.json", injuries)

    all_stats = get_all_teams_stats()
    save_data("all_teams_stats.json", all_stats)
    
    match_stats = get_spurs_match_stats()
    save_data("spurs_match_stats.json", match_stats)

    print("\n=== 완료 ===")