#!/usr/bin/env bash
set -euo pipefail

if swapon --show | grep -q '/swapfile'; then
  echo "[INFO] /swapfile is already enabled."
  exit 0
fi

echo "[INFO] Creating 4G swapfile..."
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

if ! grep -q '^/swapfile ' /etc/fstab; then
  echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
fi

echo "[INFO] Swap enabled."
