# ==========================================
# Етап 1: Збірка (Builder)
# ==========================================
FROM node:20-alpine AS builder

WORKDIR /app

# Копіюємо package.json та встановлюємо залежності
COPY package*.json ./
RUN npm install --legacy-peer-deps

# Копіюємо весь код та робимо білд (папка dist)
COPY . .

ARG VITE_API_BASE_URL
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL

RUN npm run build

# ==========================================
# Етап 2: Роздача статики (Nginx)
# ==========================================
FROM nginx:alpine

# Видаляємо дефолтну статику Nginx
RUN rm -rf /usr/share/nginx/html/*

# Копіюємо зібраний додаток з першого етапу
COPY --from=builder /app/dist /usr/share/nginx/html

# Копіюємо наш конфіг (щоб працював React Router)
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]