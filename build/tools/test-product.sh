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

Xvfb :99 -screen 0 1024x768x24 -ac >build/xvfb.log 2>&1 &
XVFB_PID=$!
export DISPLAY=:99
cleanup() {
  kill "$XVFB_PID" 2>/dev/null || true
}
trap cleanup EXIT
sleep 2

evpoll=$(sym build/zxdesk.sym EvPoll)
test -n "$evpoll"
smoke_cmd=$(printf 'breakpoint 0x%s\ncommands 1\nprint 424243\nend\n' "$evpoll")
set +e
timeout -k 5s 60s fuse --machine 48 --rom-48 assets/48.rom --auto-load --accelerate-loader --no-sound \
  --debugger-command "$smoke_cmd" build/zxdesk.tap >build/fuse-smoke.log 2>&1
smoke_rc=$?
set -e
case "$smoke_rc" in
  0|124|137) ;;
  *) exit "$smoke_rc" ;;
esac
grep -q '424243' build/fuse-smoke.log

fuse --machine 48 --rom-48 assets/48.rom --auto-load --accelerate-loader --no-sound   build/zxdesk.tap >build/fuse-visual.log 2>&1 &
FUSE_PID=$!
sleep 12
kill -0 "$FUSE_PID"
scrot shots/zxdesk.png
test "$(stat -c%s shots/zxdesk.png)" -gt 10000
kill "$FUSE_PID" 2>/dev/null || true
wait "$FUSE_PID" 2>/dev/null || true

build_one bench3 --equ BENCH=1 --equ HARNESS=1
cp build/bench3.tap build/bench3-tape.tap
python3 taplant.py build/bench3-tape.tap TAPETEST DE,AD,BE,EF,01,02,03,04

word_expr() {
  local file="$1"
  local name="$2"
  local a
  a=$(sym "$file" "$name")
  printf '([0x%s]+256*[0x%04X])' "$a" $((16#$a + 1))
}

byte_expr() {
  local file="$1"
  local name="$2"
  local a
  a=$(sym "$file" "$name")
  printf '[0x%s]' "$a"
}

bhang=$(sym build/bench3.sym BHang)
test -n "$bhang"
bsum=$(word_expr build/bench3.sym BSum)
bsum2=$(word_expr build/bench3.sym BSum2)
bsum3=$(word_expr build/bench3.sym BSum3)
bsum4=$(word_expr build/bench3.sym BSum4)
bsua=$(word_expr build/bench3.sym BSuA)
bsub=$(word_expr build/bench3.sym BSuB)
bmna=$(word_expr build/bench3.sym BMnA)
bmnb=$(word_expr build/bench3.sym BMnB)
bev=$(byte_expr build/bench3.sym BEvRes)
bhit=$(byte_expr build/bench3.sym BHitRes)
btpread=$(word_expr build/bench3.sym BTpRead)
btpsum=$(byte_expr build/bench3.sym BTpSum)
btperr=$(byte_expr build/bench3.sym BTpErr)

pass_expr="($bsum==$bsum2 && $bsum3==$bsum4 && $bsua==$bsub && $bmna==$bmnb && $bev==63 && $bhit==13 && $btpread==8 && $btpsum==66 && $btperr==0)"
bench_cmd=$(printf 'breakpoint 0x%s\ncommands 1\nprint %s\nprint %s\nprint %s\nprint %s\nprint %s\nprint %s\nprint %s\nprint %s\nprint %s\nprint 7654321+(%s)\nend\n' \
  "$bhang" "$bsum" "$bsum2" "$bsum3" "$bsum4" "$bev" "$bhit" "$btpread" "$btpsum" "$btperr" "$pass_expr")

set +e
timeout -k 5s 90s fuse --machine 48 --rom-48 assets/48.rom --auto-load --accelerate-loader --no-sound \
  --debugger-command "$bench_cmd" build/bench3-tape.tap >build/fuse-bench.log 2>&1
bench_rc=$?
set -e
case "$bench_rc" in
  0|124|137) ;;
  *) exit "$bench_rc" ;;
esac
grep -q '7654322' build/fuse-bench.log

echo "product tests passed"
