FROM node:22-trixie AS builder

WORKDIR /app

COPY package.json .
COPY package-lock.json .
RUN npm ci --legacy-peer-deps \
    && npx browserslist@latest --update-db \
    && npm cache clean --force

ARG NODE_ENV=production
ARG API_ENDPOINT

ENV NODE_ENV=$NODE_ENV
ENV VUE_APP_API_ENDPOINT=$API_ENDPOINT
COPY . .
RUN npm run build

FROM nginx:alpine

COPY config/nginx.conf /etc/nginx/nginx.conf
COPY --from=builder /app/dist /usr/share/nginx/html

RUN chown -R nginx:nginx /usr/share/nginx/html/ \
    && chmod -R 755 /usr/share/nginx/html

# Run as non-root user
USER nginx

# Add healthcheck
# HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
#     CMD wget --no-verbose --tries=1 --spider http://localhost/ || exit 1

EXPOSE 80
