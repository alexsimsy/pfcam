# Build stage
FROM node:18-alpine AS build

# Set working directory
WORKDIR /app

# Copy package files and .env first to ensure cache busting
COPY package*.json ./
COPY .env ./

# Install dependencies
RUN npm install

# Copy the rest of the source code
COPY . .

# Build the application
RUN npm run build

# Production stage
FROM node:18-alpine AS production

# Install serve globally
RUN npm install -g serve

# Set working directory
WORKDIR /app

# Copy built files from build stage
COPY --from=build /app/dist ./dist

# Expose port
EXPOSE 3000

# Start the application with proper SPA routing
CMD ["serve", "-s", "dist", "-l", "3000", "--single"] 