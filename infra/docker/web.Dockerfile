FROM node:24-slim AS deps
WORKDIR /app/apps/web
COPY apps/web/package.json ./
RUN npm install

FROM node:24-slim AS build
WORKDIR /app
COPY --from=deps /app/apps/web/node_modules ./apps/web/node_modules
COPY apps/web ./apps/web
WORKDIR /app/apps/web
RUN npm run build

FROM node:24-slim AS runtime
WORKDIR /app/apps/web
ENV NODE_ENV=production
COPY --from=build /app/apps/web ./
EXPOSE 5180
CMD ["npm", "run", "start"]
