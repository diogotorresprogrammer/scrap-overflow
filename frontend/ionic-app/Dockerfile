FROM node:20-slim AS build

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

RUN npm run build -- --configuration=production

# --- production stage ---
FROM nginx:alpine

COPY --from=build /app/www /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 8100

CMD ["nginx", "-g", "daemon off;"]
