# Multi-stage build producing Next.js's standalone output — a trimmed,
# self-contained server (its own minimal node_modules), so the final image
# doesn't carry the full dev dependency tree.

FROM node:22-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci


FROM node:22-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .

# NEXT_PUBLIC_* vars are inlined into the client JS bundle at build time —
# this is the one value that must be known now, not just at container
# runtime. It's the backend address browsers will call directly.
ARG NEXT_PUBLIC_API_BASE_URL
ENV NEXT_PUBLIC_API_BASE_URL=${NEXT_PUBLIC_API_BASE_URL}

RUN npm run build


FROM node:22-alpine AS runtime
WORKDIR /app
ENV NODE_ENV=production \
    PORT=3000 \
    HOSTNAME=0.0.0.0

RUN addgroup --system --gid 1001 nodejs \
    && adduser --system --uid 1001 nextjs

COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs
EXPOSE 3000

HEALTHCHECK --interval=15s --timeout=5s --start-period=15s --retries=5 \
    CMD wget -qO- http://localhost:3000/ >/dev/null || exit 1

CMD ["node", "server.js"]
