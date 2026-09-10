#!/bin/bash
# Phase 03 -- minimal standalone MoonRay CPU render test + runtime verification.
# Simulates a fresh shell: does not assume any variables from earlier build steps
# are still exported, only that /root/moonray-blender/install/openmoonray exists.
set -euo pipefail
INSTALL_PREFIX=/root/moonray-blender/install/openmoonray
SRC=/root/moonray-blender/src/openmoonray
OUT_DIR=/root/moonray-blender/logs
OUT_EXR="$OUT_DIR/phase03-rectangle.exr"
LOG_DIR=/root/moonray-blender/logs/phase03-build
mkdir -p "$OUT_DIR" "$LOG_DIR"

RUNTIME_LOG="$LOG_DIR/runtime-check.log"
RENDER_LOG="$LOG_DIR/render-check.log"

{
echo "=== bin listing ==="
ls -la "$INSTALL_PREFIX/bin" 2>&1
echo "=== moonray binary present? ==="
test -x "$INSTALL_PREFIX/bin/moonray" && echo "FOUND: $INSTALL_PREFIX/bin/moonray" || echo "NOT FOUND"
echo "=== ldd (looking for 'not found') ==="
ldd "$INSTALL_PREFIX/bin/moonray" 2>&1
echo "=== ldd 'not found' lines only ==="
ldd "$INSTALL_PREFIX/bin/moonray" 2>&1 | grep -i "not found" || echo "(none -- all libraries resolved)"
} > "$RUNTIME_LOG" 2>&1
cat "$RUNTIME_LOG"

export PATH="$INSTALL_PREFIX/bin:$PATH"
export RDL2_DSO_PATH="$INSTALL_PREFIX/rdl2dso"
export REZ_MOONRAY_ROOT="$INSTALL_PREFIX"

{
echo "=== moonray -help ==="
moonray -help 2>&1 || echo "(moonray -help exited non-zero: $?)"
echo "=== rendering rectangle.rdla ==="
rm -f "$OUT_EXR"
set +e
moonray -in "$SRC/testdata/rectangle.rdla" -out "$OUT_EXR"
RC=$?
set -e
echo "moonray exit code: $RC"
echo "=== output file check ==="
ls -la "$OUT_EXR" 2>&1
file "$OUT_EXR" 2>&1
echo "=== size in bytes ==="
stat -c '%s' "$OUT_EXR" 2>&1
} > "$RENDER_LOG" 2>&1
cat "$RENDER_LOG"

if [ -s "$OUT_EXR" ] && file "$OUT_EXR" | grep -qi "OpenEXR"; then
  echo "PHASE03_RENDER_OK -- $OUT_EXR"
else
  echo "PHASE03_RENDER_FAILED"
  exit 1
fi
