import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))

import json
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import matplotlib.patches as mpatches
import numpy as np

# 한글 폰트 설정 (Windows)
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

def load_data(filename):
    with open(f"data/{filename}", "r", encoding="utf-8") as f:
        return json.load(f)

fixtures_2024  = load_data("spurs_fixtures.json")
all_stats      = load_data("all_teams_stats.json")
match_stats = load_data("spurs_match_stats.json")

# ── 그래프 1. 리그 실점 순위 ──────────────────────
goals_against = []
for team_name, stats in all_stats.items():
    ga = stats["goals"]["against"]["total"]["total"]
    if ga == 0:
        continue
    goals_against.append({"team": team_name, "실점": ga})

df_goals = pd.DataFrame(goals_against).sort_values("실점", ascending=True)

fig, ax = plt.subplots(figsize=(10, 7))
colors = ["#E01010" if t == "Tottenham" else "#AAAAAA" for t in df_goals["team"]]
ax.barh(df_goals["team"], df_goals["실점"], color=colors)
ax.set_title("24/25 프리미어리그 팀별 실점 (강등팀 제외)", fontsize=14, fontweight="bold")
ax.set_xlabel("실점 수")
ax.axvline(df_goals[df_goals["team"] == "Tottenham"]["실점"].values[0], color="#E01010", linestyle="--", alpha=0.5)
plt.tight_layout()
plt.savefig("data/h1_goals_against.png", dpi=150)
plt.show()
print("그래프 1 저장 완료!")

# ── 그래프 2. 누적 승점 추이 ──────────────────────
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
        "ga":     f["goals"]["away"] if is_home else f["goals"]["home"]
    })

df_results = pd.DataFrame(results).sort_values("date").reset_index(drop=True)
df_results["라운드"]   = df_results.index + 1
df_results["누적승점"] = df_results["result"].map({"W":3,"D":1,"L":0}).cumsum()

fig, ax = plt.subplots(figsize=(12, 5))
ax.plot(df_results["라운드"], df_results["누적승점"], color="#132257", linewidth=2.5, marker="o", markersize=4)
ax.axvline(19, color="red", linestyle="--", alpha=0.6, label="전반기/후반기 구분")
ax.fill_between(df_results["라운드"], df_results["누적승점"], alpha=0.1, color="#132257")
ax.set_title("24/25 토트넘 누적 승점 추이", fontsize=14, fontweight="bold")
ax.set_xlabel("라운드")
ax.set_ylabel("누적 승점")
ax.legend()
plt.tight_layout()
plt.savefig("data/h2_points_trend.png", dpi=150)
plt.show()
print("그래프 2 저장 완료!")

# 라운드별 실제 승점 (누적 말고)
fig, ax = plt.subplots(figsize=(12, 5))
df_results["승점"] = df_results["result"].map({"W":3,"D":1,"L":0})
colors = df_results["result"].map({"W":"#2ecc71","D":"#f39c12","L":"#e74c3c"})

# 패배는 -1로 표시
display_val = df_results["result"].map({"W":3,"D":1,"L":-1})
ax.bar(df_results["라운드"], display_val, color=colors)
ax.axvline(19, color="black", linestyle="--", alpha=0.6, label="전반기/후반기 구분")
ax.axhline(0, color="black", linewidth=0.8)
ax.set_title("24/25 토트넘 라운드별 결과", fontsize=14, fontweight="bold")
ax.set_xlabel("라운드")
ax.set_yticks([-1, 1, 3])
ax.set_yticklabels(["패배", "무승부", "승리"])
ax.legend()
plt.tight_layout()
plt.savefig("data/h2_points_bar.png", dpi=150)
plt.show()
print("그래프 3 저장 완료!")

# H4 시각화

# 실점 매핑

results_map = {}
for match in fixtures_2024["response"]:
    fid = str(match["fixture"]["id"])
    is_home = match["teams"]["home"]["id"] == 47
    results_map[fid] = match["goals"]["away"] if is_home else match["goals"]["home"]

# 파싱
rows = []
for fid, stat_list in match_stats.items():
    if not stat_list:
        continue
    stats = {s["type"]: s["value"] for s in stat_list[0]["statistics"]}
    possession = float(stats.get("Ball Possession", "0%").replace("%", "") or 0)
    total_shots = stats.get("Total Shots", 0) or 0
    shots_on = stats.get("Shots on Goal", 0) or 0
    shot_accuracy = round(shots_on / total_shots * 100, 1) if total_shots > 0 else 0
    xg = float(stats.get("expected_goals", 0) or 0)
    conceded = results_map.get(fid, 0)
    rows.append({
        "possession": possession,
        "total_shots": total_shots,
        "shots_on_goal": shots_on,
        "shot_accuracy": shot_accuracy,
        "xg": xg,
        "conceded": conceded
    })

df = pd.DataFrame(rows)

fig, axes = plt.subplots(1, 3, figsize=(18, 6))
fig.suptitle("H4. 토트넘 공격 효율 & 역습 취약성 분석", fontsize=16, fontweight="bold")

# 그래프 1: 총 슈팅 vs 유효슈팅 평균 막대
ax1 = axes[0]
values = [df["total_shots"].mean(), df["shots_on_goal"].mean()]
colors = ["#1f77b4", "#d62728"]
bars = ax1.bar(["총 슈팅", "유효슈팅"], values, color=colors, width=0.5)
for bar, val in zip(bars, values):
    ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.2,
             f"{val:.1f}", ha="center", fontsize=13, fontweight="bold")
ax1.set_title("경기당 평균 슈팅 vs 유효슈팅", fontsize=13)
ax1.set_ylabel("개수")
ax1.set_ylim(0, 18)
ax1.axhline(y=df["total_shots"].mean(), color="#1f77b4", linestyle="--", alpha=0.3)
ax1.text(1, df["total_shots"].mean() + 0.3,
         f"유효슈팅 비율 {df['shot_accuracy'].mean():.1f}%", color="red", fontsize=11)

# 그래프 2: 점유율 vs 실점 산점도
ax2 = axes[1]
colors_scatter = ["#d62728" if c >= 2 else "#1f77b4" for c in df["conceded"]]
ax2.scatter(df["possession"], df["conceded"], c=colors_scatter, alpha=0.7, s=80)
ax2.axvline(x=df["possession"].mean(), color="gray", linestyle="--", alpha=0.5)
ax2.set_title("점유율 vs 실점", fontsize=13)
ax2.set_xlabel("점유율 (%)")
ax2.set_ylabel("실점")
ax2.text(df["possession"].mean() + 0.5, df["conceded"].max() - 0.2,
         f"평균 {df['possession'].mean():.1f}%", color="gray", fontsize=10)
high = mpatches.Patch(color="#d62728", label="2골 이상 실점")
low = mpatches.Patch(color="#1f77b4", label="1골 이하 실점")
ax2.legend(handles=[high, low], fontsize=10)

# 그래프 3: xG vs 실점 비교 막대
ax3 = axes[2]
values3 = [df["xg"].mean(), df["conceded"].mean()]
colors3 = ["#2ca02c", "#d62728"]
bars3 = ax3.bar(["내 xG\n(기대득점)", "실점"], values3, color=colors3, width=0.5)
for bar, val in zip(bars3, values3):
    ax3.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02,
             f"{val:.2f}", ha="center", fontsize=13, fontweight="bold")
ax3.set_title("xG vs 실점 비교\n(상대가 적은 기회로 효율적 득점)", fontsize=13)
ax3.set_ylabel("경기당 평균")
ax3.set_ylim(0, 2.5)

plt.tight_layout()
plt.savefig("data/h4_analysis.png", dpi=150, bbox_inches="tight")
print("저장 완료 → data/h4_analysis.png")
plt.show()