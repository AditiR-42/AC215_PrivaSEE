ARG TARGETPLATFORM

# Build stage
FROM --platform=${TARGETPLATFORM:-linux/amd64} node:20-alpine AS build

WORKDIR /app

# Install dependencies
COPY package.json package-lock.json ./
ENV npm_config_platform=linux
RUN npm ci

# Copy source files
COPY . .

# Build the Next.js app
RUN npm run build

# Production stage
FROM --platform=${TARGETPLATFORM:-linux/amd64} node:20-alpine AS production

WORKDIR /app

# Copy built assets from build stage
COPY --from=build /app/package.json ./package.json
COPY --from=build /app/package-lock.json ./package-lock.json
COPY --from=build /app/.next ./.next
COPY --from=build /app/public ./public

# Install only production dependencies
RUN npm ci --only=production

# Expose the listening port
EXPOSE 3000

# Define environment variable defaults for Next.js production
ENV NEXTAUTH_SECRET=change_this_default_secret

# Run the Next.js app
CMD ["npm", "start"]
