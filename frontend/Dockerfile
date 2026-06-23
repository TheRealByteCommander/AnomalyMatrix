# Build stage
FROM node:20-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --legacy-peer-deps
COPY . .
ARG VITE_API_BASE=/api/v1
ARG VITE_REQUIRE_AUTH=true
ENV VITE_API_BASE=$VITE_API_BASE
ENV VITE_REQUIRE_AUTH=$VITE_REQUIRE_AUTH
RUN npm run build

# Production stage
FROM nginx:1.27-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
