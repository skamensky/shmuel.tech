# Stage 1: Hugo build
FROM ghcr.io/gohugoio/hugo:latest AS builder
USER root
WORKDIR /site
COPY . .
# TODO: Enable Git info by building from repository root context 
# Currently disabled to keep build process consistent with other services
RUN rm -f .hugo_build.lock && \
    sed 's/enableGitInfo = true/enableGitInfo = false/' config.toml > config-docker.toml && \
    hugo --minify --config config-docker.toml

# Stage 2: Static file server
FROM nginx:alpine
COPY --from=builder /site/public /usr/share/nginx/html

# Add health check endpoint
RUN printf 'server {\n\
    listen 80;\n\
    server_name _;\n\
    root /usr/share/nginx/html;\n\
    index index.html index.htm;\n\
\n\
    # Health check endpoint\n\
    location /health {\n\
        access_log off;\n\
        return 200 "OK\\n";\n\
        add_header Content-Type text/plain;\n\
    }\n\
\n\
    # Serve static files\n\
    location / {\n\
        try_files $uri $uri/ =404;\n\
    }\n\
}\n' > /etc/nginx/conf.d/default.conf