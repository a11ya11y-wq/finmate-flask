# Етап 1: Збірка
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

# Етап 2: Фінальний образ
FROM node:20-alpine
WORKDIR /app

# 1. Встановлюємо Chromium та залежності
RUN apk add --no-cache \
      chromium \
      nss \
      freetype \
      harfbuzz \
      ca-certificates \
      ttf-freefont

# 2. Кажемо Puppeteer використовувати системний Chromium замість завантаження свого
ENV PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true \
    PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium-browser

COPY package*.json ./
RUN npm install --only=production

# Копіюємо скомпілений код та шаблони[cite: 1]
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/templates ./templates

# Створюємо папку для волюма, щоб не було помилок доступу[cite: 1]
RUN mkdir -p /app/uploads && chmod 777 /app/uploads

CMD ["node", "dist/main"]