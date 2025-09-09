FROM node:18-alpine

WORKDIR /app

# Копирование package.json и установка зависимостей
COPY package.json package-lock.json* ./
RUN npm ci --only=production

# Копирование исходного кода
COPY server.js ./

# Создание пользователя для безопасности
RUN addgroup -g 1001 -S nodejs
RUN adduser -S nodejs -u 1001
USER nodejs

EXPOSE 3000

CMD ["node", "server.js"]