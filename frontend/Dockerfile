# Build stage — Debian (not Alpine): Vite 8 / rolldown needs glibc native bindings
FROM node:26-bookworm-slim AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --legacy-peer-deps
COPY . .
ARG VITE_API_BASE=/api/v1
ARG VITE_REQUIRE_AUTH=true
ARG VITE_DEV_AUTH_HEADERS=false
ENV VITE_API_BASE=$VITE_API_BASE
ENV VITE_REQUIRE_AUTH=$VITE_REQUIRE_AUTH
ENV VITE_DEV_AUTH_HEADERS=$VITE_DEV_AUTH_HEADERS
RUN npm run build

# Production stage
FROM nginx:1.31-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
