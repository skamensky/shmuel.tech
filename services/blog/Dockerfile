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