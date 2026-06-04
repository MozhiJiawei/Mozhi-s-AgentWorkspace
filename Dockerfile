ARG NODE_IMAGE=node:24.13.1-alpine3.22
FROM ${NODE_IMAGE}
ARG ALPINE_MIRROR=

LABEL org.opencontainers.image.title="Mozhi Agent Workspace Docs"
LABEL org.opencontainers.image.description="Runtime image for building and serving the workspace documentation site from mounted repository content."
LABEL org.opencontainers.image.base.name="node:24.13.1-alpine3.22"

RUN if [ -n "$ALPINE_MIRROR" ]; then \
      sed -i "s|https://dl-cdn.alpinelinux.org/alpine|$ALPINE_MIRROR|g" /etc/apk/repositories; \
    fi \
    && apk add --no-cache nginx python3 rsync tini

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY docker/nginx.conf /etc/nginx/nginx.conf
COPY docker/entrypoint.sh /usr/local/bin/mozhi-docs-entrypoint
RUN chmod +x /usr/local/bin/mozhi-docs-entrypoint \
    && mkdir -p /site /run/nginx /var/lib/nginx /var/log/nginx

EXPOSE 8080

ENTRYPOINT ["tini", "--", "/usr/local/bin/mozhi-docs-entrypoint"]
