FROM node:24-slim AS deps
WORKDIR /app/apps/web
COPY apps/web/package*.json ./
RUN npm ci

FROM node:24-slim AS build
WORKDIR /app
COPY --from=deps /app/apps/web/node_modules ./apps/web/node_modules
COPY apps/web ./apps/web
WORKDIR /app/apps/web
RUN npm run build

FROM node:24-slim AS runtime
WORKDIR /app/apps/web
ENV NODE_ENV=production
COPY --from=build /app/apps/web/package*.json ./
COPY --from=build /app/apps/web/.next ./.next
COPY --from=build /app/apps/web/public ./public
COPY --from=build /app/apps/web/node_modules ./node_modules
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 CMD node -e "fetch('http://127.0.0.1:5180').then(r=>process.exit(r.ok?0:1)).catch(()=>process.exit(1))"
EXPOSE 5180
CMD ["npm", "run", "start"]
