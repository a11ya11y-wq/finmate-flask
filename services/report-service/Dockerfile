# === БАЗОВИЙ ОБРАЗ (Переходимо на Debian slim заради Playwright) ===
FROM node:20-bookworm-slim AS base
WORKDIR /app

# Копіюємо маніфести пакетів
COPY package*.json ./

# Встановлюємо пакети (це стягне саму лібу playwright)
RUN npm install

# МАГІЯ PLAYWRIGHT: Офіційна команда, яка сама ставить Chromium 
# і ВСІ необхідні системні залежності Debian (шрифти, libnss тощо)
RUN npx playwright install --with-deps chromium

# === ЕТАП РОЗРОБКИ (Target: development) ===
FROM base AS development
COPY . .
RUN mkdir -p /app/uploads && chmod 777 /app/uploads
CMD ["npm", "run", "start:dev"]

# === ЕТАП ЗБІРКИ ===
FROM base AS builder
COPY . .
RUN npm run build

# === ФІНАЛЬНИЙ ПРОДАКШЕН ОБРАЗ (Target: production) ===
FROM base AS production
# Видаляємо dev-залежності для економії місця
RUN npm prune --production
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/templates ./templates
RUN mkdir -p /app/uploads && chmod 777 /app/uploads

CMD ["node", "dist/main"]