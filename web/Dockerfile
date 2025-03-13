FROM node:18-bookworm AS builder

WORKDIR /app

COPY package.json .
COPY package-lock.json .
RUN npm ci --legacy-peer-deps

ARG NODE_ENV
ARG API_ENDPOINT

ENV NODE_ENV=$NODE_ENV
ENV VUE_APP_API_ENDPOINT=$API_ENDPOINT
ENV NODE_OPTIONS=--openssl-legacy-provider

COPY . .
RUN npm run build

FROM nginx

COPY config/nginx.conf /etc/nginx/nginx.conf
COPY --from=builder /app/dist /usr/share/nginx/html

RUN chown -R nginx:nginx /usr/share/nginx/html/
