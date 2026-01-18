FROM --platform=$BUILDPLATFORM oven/bun:1-alpine AS deps
WORKDIR /app
COPY package.json bun.lockb* ./
RUN bun install --frozen-lockfile

FROM --platform=$BUILDPLATFORM oven/bun:1-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN bun run build

FROM --platform=$BUILDPLATFORM golang:1.21-alpine AS server-builder
ARG TARGETOS
ARG TARGETARCH
ARG TARGETVARIANT
WORKDIR /build
COPY server.go go.mod ./
COPY --from=builder /app/dist ./dist
RUN CGO_ENABLED=0 GOOS=${TARGETOS} GOARCH=${TARGETARCH} GOARM=${TARGETVARIANT#v} \
    go build -ldflags="-s -w" -trimpath -o server .

FROM scratch
COPY --from=server-builder /build/server /server
EXPOSE 3000
ENTRYPOINT ["/server"]
