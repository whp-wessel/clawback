#!/usr/bin/env bash
# infra/setup-lfs-server.sh — Bootstrap the LFS server on a fresh Hetzner VPS
# Run this ON THE VPS after SSH-ing in: bash setup-lfs-server.sh <S3_ACCESS_KEY> <S3_SECRET_KEY> <S3_ENDPOINT> <S3_BUCKET>
set -euo pipefail

if [ $# -lt 4 ]; then
  echo "Usage: $0 <S3_ACCESS_KEY> <S3_SECRET_KEY> <S3_ENDPOINT> <S3_BUCKET>"
  exit 1
fi

S3_ACCESS_KEY="$1"
S3_SECRET_KEY="$2"
S3_ENDPOINT="$3"
S3_BUCKET="$4"

echo "=== Installing Docker ==="
curl -fsSL https://get.docker.com | sh
systemctl enable docker
systemctl start docker

echo "=== Pulling and starting rudolfs ==="
docker run -d \
  --name rudolfs \
  --restart always \
  -p 8080:8080 \
  -e AWS_ACCESS_KEY_ID="$S3_ACCESS_KEY" \
  -e AWS_SECRET_ACCESS_KEY="$S3_SECRET_KEY" \
  -e AWS_DEFAULT_REGION="fsn1" \
  jasonwhite/rudolfs:latest \
  --s3-bucket "$S3_BUCKET" \
  --s3-endpoint "$S3_ENDPOINT" \
  --host 0.0.0.0:8080

echo "=== Setting up firewall (allow 80, 443, 22, 8080) ==="
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 8080/tcp
ufw --force enable

echo "=== Done ==="
echo "LFS server running on port 8080"
echo "Test: curl http://$(hostname -I | awk '{print $1}'):8080"
