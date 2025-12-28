# Multi-stage build for frontend
FROM node:20-alpine AS builder

WORKDIR /app

# Copy only package files (cacheable layer)
COPY package*.json ./

# Install dependencies (cached until package*.json changes)
RUN npm ci --legacy-peer-deps

# Copy source code (invalidates cache only if code changes)
COPY tsconfig.json tsconfig.node.json vite.config.ts postcss.config.js tailwind.config.js ./
COPY src ./src
COPY public ./public
COPY index.html ./

# Build application
RUN npm run build

# Production stage - serve with Node
FROM node:20-alpine

WORKDIR /app

# Install serve to run the static site
RUN npm install -g serve

# Copy built app from builder
COPY --from=builder /app/dist ./dist

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD node -e "require('http').get('http://localhost:3000', (r) => {if (r.statusCode !== 200) throw new Error(r.statusCode)})"

# Start application
CMD ["serve", "-s", "dist", "-l", "3000"]
