import requests
from config import BASE_URL, HEADERS

response = requests.get(f"{BASE_URL}/status", headers=HEADERS)
data = response.json()

print("연결 성공 ✅")
print(f"플랜: {data['response']['subscription']['plan']}")
print(f"오늘 사용한 콜: {data['response']['requests']['current']}")
print(f"남은 콜: {data['response']['requests']['limit_day']}")
