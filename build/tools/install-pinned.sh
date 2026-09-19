#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
TOOLS="$ROOT/build/tools"
CACHE="$TOOLS/cache"
mkdir -p "$CACHE"

source "$TOOLS/toolchain.env"

printf 'APT::Snapshot "%s";\n' "$UBUNTU_SNAPSHOT" > /etc/apt/apt.conf.d/50zxdesk-snapshot
apt-get update
apt-get install -y --no-install-recommends build-essential ca-certificates wget

fetch() {
  local url="$1"
  local sha="$2"
  local name="$3"
  local out="$CACHE/$name"
  wget -q -O "$out" "$url"
  printf '%s  %s\n' "$sha" "$out" | sha256sum -c -
}

fetch "$FUSE_PACKAGE_URL" "$FUSE_PACKAGE_SHA256" "fuse-emulator-gtk.deb"
fetch "$XVFB_PACKAGE_URL" "$XVFB_PACKAGE_SHA256" "xvfb.deb"
fetch "$SCROT_PACKAGE_URL" "$SCROT_PACKAGE_SHA256" "scrot.deb"
fetch "$PASMO_URL" "$PASMO_SHA256" "pasmo-$PASMO_VERSION.tar.gz"

apt-get install -y --no-install-recommends   "$CACHE/fuse-emulator-gtk.deb"   "$CACHE/xvfb.deb"   "$CACHE/scrot.deb"

cd "$CACHE"
rm -rf "pasmo-$PASMO_VERSION"
tar xzf "pasmo-$PASMO_VERSION.tar.gz"
cd "pasmo-$PASMO_VERSION"
./configure
make -j1
make install

command -v pasmo
fuse --version
scrot --version
