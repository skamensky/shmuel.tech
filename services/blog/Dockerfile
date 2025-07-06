# Stage 1: Hugo build
FROM klakegg/hugo:0.124.1-ext-alpine AS builder
WORKDIR /site
COPY . .
RUN hugo --minify

# Stage 2: Static file server
FROM nginx:alpine
COPY --from=builder /site/public /usr/share/nginx/html