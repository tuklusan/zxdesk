#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
TOOLS="$ROOT/build/tools"
CACHE="$TOOLS/cache"
mkdir -p "$CACHE"

source "$TOOLS/toolchain.env"

fetch() {
  local url="$1"
  local sha="$2"
  local name="$3"
  local out="$CACHE/$name"
  wget -q -O "$out" "$url"
  printf '%s  %s\n' "$sha" "$out" | sha256sum -c -
}

fetch "$PASMO_URL" "$PASMO_SHA256" "pasmo-$PASMO_VERSION.tar.gz"
fetch "$FUSE_SOURCE_URL" "$FUSE_SOURCE_SHA256" "fuse-$FUSE_VERSION.tar.gz"
fetch "$XVFB_SOURCE_URL" "$XVFB_SOURCE_SHA256" "xorg-server-21.1.12.tar.xz"
fetch "$SCROT_SOURCE_URL" "$SCROT_SOURCE_SHA256" "scrot-1.10.tar.gz"
fetch "$UPEEP80_URL" "$UPEEP80_SHA256" "upeep80-$UPEEP80_VERSION.tar.gz"
