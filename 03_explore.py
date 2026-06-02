import json
import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# JSON 파일 불러오기
def load_data(filename):
    with open(f"data/{filename}", "r", encoding="utf-8") as f:
        return json.load(f)

spurs_stats    = load_data("spurs_stats.json")
spurs_injuries = load_data("spurs_injuries.json")
spurs_fixtures = load_data("spurs_fixtures.json")

# 1. 팀 통계 어떤 항목 있는지 확인
print("=== 팀 통계 키 목록 ===")
response = spurs_stats["response"]
for key in response.keys():
    print(f"  - {key}")

# 2. 부상자 데이터 확인
print(f"\n=== 부상자 데이터 ===")
print(f"총 부상 기록 수: {spurs_injuries['results']}")
if spurs_injuries["results"] > 0:
    print("첫 번째 부상 기록:")
    print(json.dumps(spurs_injuries["response"][0], indent=2, ensure_ascii=False))

# 3. 경기 수 확인
print(f"\n=== 경기 데이터 ===")
print(f"총 경기 수: {spurs_fixtures['results']}")
if spurs_fixtures["results"] > 0:
    first = spurs_fixtures["response"][0]
    print(f"첫 경기: {first['teams']['home']['name']} vs {first['teams']['away']['name']}")
    print(f"결과: {first['goals']['home']} - {first['goals']['away']}")