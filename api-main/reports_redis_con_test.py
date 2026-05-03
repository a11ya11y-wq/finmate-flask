import redis
import json
import uuid

# Підключення до Redis
r = redis.Redis(host='localhost', port=6379, db=0)

# Дані для звіту
payload = {
    "data": {
        "userId": 7,
        "startDate": "2025-05-30",
        "endDate": "2026-05-10"
    }
}

# Відправляємо в канал, який слухає NestJS
# За замовчуванням NestJS для повідомлень з відповіддю використовує назву патерну як рядок
# Або канал за замовчуванням (залежить від налаштувань)
channel = 'reports_queue' # Якщо ти не міняв налаштування, спробуй спочатку назву ресурсу

print(f"🚀 Відправка задачі в NestJS...")
r.publish(channel, json.dumps(payload))
print("✅ Повідомлення відправлено. Перевір консоль NestJS!")