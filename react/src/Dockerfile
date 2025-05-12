# Stage 1: Build the app
FROM node:23-slim AS builder

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm install
RUN npm i --save-dev @types/react-syntax-highlighter


# Copy source code
COPY . .

# Build the app
RUN npm run build

# Stage 2: Serve with nginx
FROM nginx:alpine

# Copy the build output to nginx's public directory
COPY --from=builder /app/dist /usr/share/nginx/html

# Replace default nginx config with a minimal one for SPAs
COPY nginx.conf /etc/nginx/conf.d/default.conf


# Expose port 80
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
