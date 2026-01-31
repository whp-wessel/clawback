#!/usr/bin/env bash
# infra/provision-hetzner.sh — Create VPS + Object Storage on Hetzner
# Prerequisites: hcloud CLI installed and authenticated (hcloud context create clawback)
set -euo pipefail

PROJECT_NAME="clawback"
SERVER_NAME="clawback-lfs"
SERVER_TYPE="cx22"          # 2 vCPU, 4 GB RAM, 40 GB disk — 3.99 EUR/mo
IMAGE="ubuntu-24.04"
LOCATION="fsn1"             # Falkenstein — same region as Object Storage

# Check hcloud is configured
if ! hcloud context active &>/dev/null; then
  echo "ERROR: No active hcloud context. Run:"
  echo "  hcloud context create $PROJECT_NAME"
  echo "  (paste your API token when prompted)"
  exit 1
fi

# Create SSH key if not already uploaded
SSH_KEY_NAME="clawback-deploy"
if ! hcloud ssh-key describe "$SSH_KEY_NAME" &>/dev/null; then
  echo "=== Uploading SSH key ==="
  if [ -f ~/.ssh/id_ed25519.pub ]; then
    hcloud ssh-key create --name "$SSH_KEY_NAME" --public-key-from-file ~/.ssh/id_ed25519.pub
  elif [ -f ~/.ssh/id_rsa.pub ]; then
    hcloud ssh-key create --name "$SSH_KEY_NAME" --public-key-from-file ~/.ssh/id_rsa.pub
  else
    echo "ERROR: No SSH public key found in ~/.ssh/"
    echo "Generate one: ssh-keygen -t ed25519"
    exit 1
  fi
fi

# Create server
echo "=== Creating server: $SERVER_NAME ==="
hcloud server create \
  --name "$SERVER_NAME" \
  --type "$SERVER_TYPE" \
  --image "$IMAGE" \
  --location "$LOCATION" \
  --ssh-key "$SSH_KEY_NAME"

SERVER_IP=$(hcloud server ip "$SERVER_NAME")
echo ""
echo "=== Server created ==="
echo "IP: $SERVER_IP"
echo ""
echo "=== Next steps ==="
echo ""
echo "1. Create Object Storage bucket in Hetzner Cloud Console:"
echo "   https://console.hetzner.cloud → Object Storage → Create Bucket"
echo "   Name: clawback-lfs"
echo "   Region: eu-central (fsn1)"
echo "   Note the S3 credentials (Access Key + Secret Key)"
echo ""
echo "2. SSH into the server and run the setup script:"
echo "   scp infra/setup-lfs-server.sh root@$SERVER_IP:~/"
echo "   ssh root@$SERVER_IP"
echo "   bash setup-lfs-server.sh <ACCESS_KEY> <SECRET_KEY> <S3_ENDPOINT> clawback-lfs"
echo ""
echo "3. Test the LFS server:"
echo "   curl http://$SERVER_IP:8080"
echo ""
echo "4. Configure the repo:"
echo "   Add to .lfsconfig:"
echo "   [lfs]"
echo "       url = http://$SERVER_IP:8080"
