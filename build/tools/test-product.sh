#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
mkdir -p build shots

sym() {
  local file="$1"
  local name="$2"
  awk -v n="$name" '$1==n {v=$3; sub(/[Hh]$/,"",v); print v; exit}' "$file"
}

build_one() {
  local name="$1"
  shift
  pasmo -I src "$@" --name "$name.tap" --tapbas src/zxdesk.asm "build/$name.tap" "build/$name.sym"
  pasmo -I src "$@" --bin src/zxdesk.asm "build/$name.bin"
  test -s "build/$name.tap"
  test -s "build/$name.bin"
  local bytes end slowend
  bytes=$(stat -c%s "build/$name.bin")
  end=$((0x6000 + bytes))
  slowend=$(sym "build/$name.sym" SlowEnd)
  slowend=$((16#${slowend:-6000}))
  test "$end" -le $((0xBD00))
  test "$slowend" -le $((0x8000))
}

build_one zxdesk
build_one zxtest --equ TEST=1 --equ HARNESS=1

python3 -m py_compile taplant.py tstates.py zxtest.py
PYTHONPATH="$ROOT/build/tools/python" python3 zxtest.py | tee build/zxtest.log
PYTHONPATH="$ROOT/build/tools/python" python3 zxtest.py --shot | tee build/zxshot.log
test -s shots/headless-notepad.png

install -d /usr/local/share/spectrum-roms
install -m 0644 assets/48.rom /usr/local/share/spectrum-roms/48.rom
printf '%s  %s\n' d55daa439b673b0e3f5897f99ac37ecb45f974d1862b4dadb85dec34af99cb42 /usr/local/share/spectrum-roms/48.rom | sha256sum -c -

Xvfb :99 -screen 0 1024x768x24 -ac >build/xvfb.log 2>&1 &
XVFB_PID=$!
export DISPLAY=:99

stop_proc() {
  local pid="$1"
  kill "$pid" 2>/dev/null || true
  for _ in 1 2 3 4 5 6 7 8 9 10; do
    if ! kill -0 "$pid" 2>/dev/null; then
      wait "$pid" 2>/dev/null || true
      return
    fi
    sleep 0.2
  done
  kill -KILL "$pid" 2>/dev/null || true
  wait "$pid" 2>/dev/null || true
}

cleanup() {
  stop_proc "$XVFB_PID"
}
trap cleanup EXIT
sleep 2

fuse --machine 48 --auto-load --phantom-typist-mode Keyword --accelerate-loader --no-sound \
  --tape build/zxdesk.tap >build/fuse-visual.log 2>&1 &
FUSE_PID=$!
sleep 12
kill -0 "$FUSE_PID"
scrot shots/zxdesk.png
python3 build/tools/check-screen.py nonblank shots/zxdesk.png
stop_proc "$FUSE_PID"

build_one bench3 --equ BENCH=1 --equ HARNESS=1
cp build/bench3.tap build/bench3-tape.tap
python3 taplant.py build/bench3-tape.tap TAPETEST DE,AD,BE,EF,01,02,03,04

fuse --full-screen --machine 48 --auto-load --phantom-typist-mode Keyword --accelerate-loader --no-sound \
  --tape build/bench3-tape.tap >build/fuse-bench.log 2>&1 &
FUSE_PID=$!
sleep 18
kill -0 "$FUSE_PID"
scrot shots/bench3.png
python3 build/tools/check-screen.py green shots/bench3.png
stop_proc "$FUSE_PID"

echo "product tests passed"
