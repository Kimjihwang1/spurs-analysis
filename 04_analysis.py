import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))

import json
import pandas as pd

def load_data(filename):
    with open(f"data/{filename}", "r", encoding="utf-8") as f:
        return json.load(f)

# 데이터 불러오기
injuries_2024 = load_data("spurs_injuries.json")
injuries_2023 = load_data("spurs_injuries_2023.json")
fixtures_2024 = load_data("spurs_fixtures.json")

# 1. 부상 vs 정지 분리
def parse_injuries(data):
    records = []
    for item in data["response"]:
        records.append({
            "player": item["player"]["name"],
            "type":   item["player"]["type"],
            "reason": item["player"]["reason"],
            "date":   item["fixture"]["date"][:10]
        })
    return pd.DataFrame(records)

df_2024 = parse_injuries(injuries_2024)
df_2023 = parse_injuries(injuries_2023)

# 2. 진짜 부상만 필터링
real_2024 = df_2024[df_2024["reason"] != "Suspended"]
real_2023 = df_2023[df_2023["reason"] != "Suspended"]

print("=== 부상 비교 (정지 제외) ===")
print(f"23/24 시즌 부상: {len(real_2023)}건")
print(f"24/25 시즌 부상: {len(real_2024)}건")

# 3. 부상 유형별 분류
print("\n=== 24/25 부상 유형 Top 10 ===")
print(real_2024["reason"].value_counts().head(10))

print("\n=== 23/24 부상 유형 Top 10 ===")
print(real_2023["reason"].value_counts().head(10))

# 4. 경기 성적 추이
results = []
for f in fixtures_2024["response"]:
    home = f["teams"]["home"]
    away = f["teams"]["away"]
    is_home = home["id"] == 47
    if is_home:
        result = "W" if home["winner"] else ("L" if away["winner"] else "D")
    else:
        result = "W" if away["winner"] else ("L" if home["winner"] else "D")
    results.append({
        "date":   f["fixture"]["date"][:10],
        "result": result,
        "gf":     f["goals"]["home"] if is_home else f["goals"]["away"],
        "ga":     f["goals"]["away"] if is_home else f["goals"]["home"]
    })

df_results = pd.DataFrame(results).sort_values("date").reset_index(drop=True)
df_results["누적승점"] = df_results["result"].map({"W":3,"D":1,"L":0}).cumsum()

print("\n=== 시즌 성적 요약 ===")
print(df_results["result"].value_counts())
print(f"\n최종 누적 승점: {df_results['누적승점'].iloc[-1]}점")

# 5. H1 - 리그 전체 실점 비교
all_stats = load_data("all_teams_stats.json")

goals_against = []
for team_name, stats in all_stats.items():
    ga = stats["goals"]["against"]["total"]["total"]
    gf = stats["goals"]["for"]["total"]["total"]
    goals_against.append({
        "team": team_name,
        "실점": ga,
        "득점": gf
    })

df_goals = pd.DataFrame(goals_against).sort_values("실점", ascending=False)
print("=== H1. 리그 실점 순위 ===")
print(df_goals.to_string(index=False, max_rows=None))
pd.set_option('display.max_rows', None)

# 6. H2 - 시즌 전/후반부 성적 비교
df_results["라운드"] = df_results.index + 1
first_half  = df_results[df_results["라운드"] <= 19]
second_half = df_results[df_results["라운드"] >= 20]

print("\n=== H2. 전반기 vs 후반기 성적 ===")
print("전반기(1~19라운드):")
print(first_half["result"].value_counts())
print(f"승점: {first_half['result'].map({'W':3,'D':1,'L':0}).sum()}점")

print("\n후반기(20~38라운드):")
print(second_half["result"].value_counts())
print(f"승점: {second_half['result'].map({'W':3,'D':1,'L':0}).sum()}점")

# 7. H3 - 전반전 vs 후반전 실점
ht_goals_against = 0
ft_goals_against = 0

for f in fixtures_2024["response"]:
    is_home = f["teams"]["home"]["id"] == 47
    ht = f["score"]["halftime"]
    ft = f["score"]["fulltime"]
    
    if ht["home"] is None:
        continue
        
    if is_home:
        ht_ga = ht["away"]
        ft_ga = ft["away"] - ht["away"]
    else:
        ht_ga = ht["home"]
        ft_ga = ft["home"] - ht["home"]
    
    ht_goals_against += ht_ga
    ft_goals_against += ft_ga
    
    # 8. H4 - 점유율 높은데 역습 허용 패턴
match_stats = load_data("spurs_match_stats.json")

# 경기 결과 (실점) 매핑
results_map = {}
for match in fixtures_2024["response"]:
    fid = str(match["fixture"]["id"])
    is_home = match["teams"]["home"]["id"] == 47
    if is_home:
        conceded = match["goals"]["away"]
    else:
        conceded = match["goals"]["home"]
    results_map[fid] = conceded

# 경기별 데이터 파싱
rows = []
for fid, stat_list in match_stats.items():
    if not stat_list:
        continue
    stats = {s["type"]: s["value"] for s in stat_list[0]["statistics"]}

    possession = stats.get("Ball Possession", "0%")
    possession = float(possession.replace("%", "")) if possession else None

    total_shots = stats.get("Total Shots", 0) or 0
    shots_on = stats.get("Shots on Goal", 0) or 0
    shot_accuracy = round(shots_on / total_shots * 100, 1) if total_shots > 0 else 0
    xg = float(stats.get("expected_goals", 0) or 0)
    conceded = results_map.get(fid, 0)

    rows.append({
        "fixture_id": fid,
        "possession": possession,
        "total_shots": total_shots,
        "shots_on_goal": shots_on,
        "shot_accuracy": shot_accuracy,
        "xg": xg,
        "conceded": conceded
    })

df_h4 = pd.DataFrame(rows)

print("\n=== H4. 토트넘 시즌 평균 ===")
print(f"평균 점유율: {df_h4['possession'].mean():.1f}%")
print(f"평균 총 슈팅: {df_h4['total_shots'].mean():.1f}")
print(f"평균 유효슈팅: {df_h4['shots_on_goal'].mean():.1f}")
print(f"평균 유효슈팅 비율: {df_h4['shot_accuracy'].mean():.1f}%")
print(f"평균 xG: {df_h4['xg'].mean():.2f}")
print(f"평균 실점: {df_h4['conceded'].mean():.2f}")

print("\n=== H4. 점유율 높은 경기(60%↑) vs 낮은 경기 실점 비교 ===")
high_poss = df_h4[df_h4["possession"] >= 60]["conceded"].mean()
low_poss = df_h4[df_h4["possession"] < 60]["conceded"].mean()
print(f"점유율 60% 이상 경기 평균 실점: {high_poss:.2f}")
print(f"점유율 60% 미만 경기 평균 실점: {low_poss:.2f}")

print("\n=== H3. 전반전 vs 후반전 실점 ===")
print(f"전반전 실점: {ht_goals_against}")
print(f"후반전 실점: {ft_goals_against}")
print(f"후반전 실점 비율: {ft_goals_against/(ht_goals_against+ft_goals_against)*100:.1f}%")