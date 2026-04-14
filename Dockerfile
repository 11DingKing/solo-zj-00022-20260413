FROM node:14-slim AS frontend-builder

WORKDIR /app
COPY package.json package-lock.json ./
RUN npm install --ignore-scripts \
    && npm uninstall node-sass \
    && npm install sass@1.57.1 --save \
    && npm install sass-loader@7.3.1 --save --legacy-peer-deps
COPY webpack.config.js webpack-stats.json* .babelrc ./
COPY src ./src
COPY public ./public
RUN npm run build

FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
COPY --from=frontend-builder /app/dist ./dist
COPY --from=frontend-builder /app/webpack-stats.json ./webpack-stats.json

RUN python -c "import django; django.setup()" 2>/dev/null || true

EXPOSE 8000

CMD ["sh", "-c", "python manage.py migrate && python manage.py runserver 0.0.0.0:8000"]
