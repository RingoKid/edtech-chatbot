# --- Stage 1: Build React Frontend (Builder Stage) ---
# Use the official Node.js 22 LTS (Long-Term Support) image.
FROM public.ecr.aws/docker/library/node:22-alpine AS builder

# Set the working directory within the builder stage.
WORKDIR /app

# Copy package manifests and install dependencies first to leverage Docker's layer caching.
COPY package*.json ./
RUN npm install

# Copy the rest of the frontend source code and build the application.
COPY . ./
RUN npm run build

# --- Stage 2: Production Stage with Nginx ---
# Use nginx:alpine for serving static files
FROM public.ecr.aws/docker/library/nginx:alpine

# Copy the built React app from the builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy custom nginx configuration if needed (optional)
# COPY nginx.conf /etc/nginx/nginx.conf

# Expose port 80 for nginx
EXPOSE 80

# Start nginx (this is the default command for nginx:alpine)
CMD ["nginx", "-g", "daemon off;"]
