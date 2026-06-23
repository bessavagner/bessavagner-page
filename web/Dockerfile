# --- Build stage (pnpm via corepack; glibc base matches the lockfile) ---
FROM node:22-slim AS build
WORKDIR /app
RUN corepack enable
COPY package.json pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile
COPY . .
# Build-time public envs (baked into the static output).
ARG PUBLIC_WEB3FORMS_KEY=""
ENV PUBLIC_WEB3FORMS_KEY=$PUBLIC_WEB3FORMS_KEY
ARG PUBLIC_ANALYTICS_WEBSITE_ID=""
ENV PUBLIC_ANALYTICS_WEBSITE_ID=$PUBLIC_ANALYTICS_WEBSITE_ID
ARG PUBLIC_ANALYTICS_SRC=""
ENV PUBLIC_ANALYTICS_SRC=$PUBLIC_ANALYTICS_SRC
RUN pnpm build

# --- Serve stage (static via nginx, Cloud Run listens on 8080) ---
FROM nginx:1.27-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 8080
CMD ["nginx", "-g", "daemon off;"]
