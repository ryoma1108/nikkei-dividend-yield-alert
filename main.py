import requests
import os

GAS_URL = os.environ["GAS_WEBHOOK_URL"]

message = "🎉 GitHubからLINE通知テスト成功！"

response = requests.post(GAS_URL, data=message)

print(response.text)
