FROM node:22-alpine AS build

WORKDIR /app

ARG HTTP_PROXY=
ARG HTTPS_PROXY=
ARG NO_PROXY=localhost,127.0.0.1
ARG NPM_CONFIG_REGISTRY=https://registry.npmjs.org/
ARG NPM_CONFIG_PROXY=
ARG NPM_CONFIG_HTTPS_PROXY=
ARG NPM_CONFIG_STRICT_SSL=true
ARG VITE_API_BASE_URL=/api
ARG VITE_API_MOCKS=false
ARG VITE_REALTIME_URL=

ENV HTTP_PROXY=${HTTP_PROXY}
ENV HTTPS_PROXY=${HTTPS_PROXY}
ENV NO_PROXY=${NO_PROXY}
ENV NPM_CONFIG_REGISTRY=${NPM_CONFIG_REGISTRY}
ENV NPM_CONFIG_PROXY=${NPM_CONFIG_PROXY}
ENV NPM_CONFIG_HTTPS_PROXY=${NPM_CONFIG_HTTPS_PROXY}
ENV NPM_CONFIG_STRICT_SSL=${NPM_CONFIG_STRICT_SSL}
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}
ENV VITE_API_MOCKS=${VITE_API_MOCKS}
ENV VITE_REALTIME_URL=${VITE_REALTIME_URL}

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM nginx:1.27-alpine AS runtime

RUN rm -f /etc/nginx/conf.d/default.conf \
    && sed -i -E \
        -e 's#pid[[:space:]]+(/var)?/run/nginx.pid;#pid /tmp/nginx.pid;#' \
        -e 's#^user[[:space:]]+[^;]+;##' \
        /etc/nginx/nginx.conf \
    && mkdir -p /var/cache/nginx /var/run /usr/share/nginx/html \
    && chown -R nginx:nginx /var/cache/nginx /var/run /usr/share/nginx/html /etc/nginx/conf.d

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build --chown=nginx:nginx /app/dist /usr/share/nginx/html

EXPOSE 8080

USER nginx

ENTRYPOINT []

CMD ["nginx", "-g", "daemon off;"]
