FROM node:22-alpine AS frontend
WORKDIR /build
COPY reservation-app/package*.json ./
RUN npm ci
COPY reservation-app/ ./
RUN npm run build

FROM python:3.12-slim
WORKDIR /app
COPY requirements-render.txt ./
RUN pip install --no-cache-dir -r requirements-render.txt
COPY . .
COPY --from=frontend /build/dist /app/reservation-app/dist

ENV DB_PATH=/var/data/app.db
CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:${PORT:-10000} --workers 1 wsgi:app"]
