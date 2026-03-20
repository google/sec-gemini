FROM node:lts AS build
WORKDIR /app
COPY . .

# Install dependencies
RUN npm install

# Copy and build app
RUN npm run build

FROM nginx:alpine AS runtime
COPY ./nginx/nginx.conf /etc/nginx/nginx.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 8080
