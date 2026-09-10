#!/bin/bash
# Phase 03 -- minimal standalone MoonRay CPU render test + runtime verification.
# Simulates a fresh shell: does not assume any variables from earlier build steps
# are still exported, only that /root/moonray-blender/install/openmoonray exists.
#
# Output path is overridable via PHASE03_OUT_EXR so a re-verification run does not
# clobber the recorded evidence artifact (logs/phase03-rectangle.exr, whose sha256 is
# pinned in docs/evidence/phase03/README.md). Default stays the documented path.
set -euo pipefail
INSTALL_PREFIX=/root/moonray-blender/install/openmoonray
SRC=/root/moonray-blender/src/openmoonray
DEPS_ROOT=/opt/MoonRay/installs
OUT_DIR=/root/moonray-blender/logs
OUT_EXR="${PHASE03_OUT_EXR:-$OUT_DIR/phase03-rectangle.exr}"
LOG_DIR=/root/moonray-blender/logs/phase03-build
mkdir -p "$OUT_DIR" "$LOG_DIR" "$(dirname "$OUT_EXR")"

RUNTIME_LOG="$LOG_DIR/runtime-check.log"
RENDER_LOG="$LOG_DIR/render-check.log"

fail() { echo "PHASE03_RENDER_FAILED: $*" >&2; exit 1; }

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

test -x "$INSTALL_PREFIX/bin/moonray" || fail "moonray binary missing or not executable"
if ldd "$INSTALL_PREFIX/bin/moonray" 2>&1 | grep -qi "not found"; then
  fail "unresolved shared libraries -- see $RUNTIME_LOG"
fi

export PATH="$INSTALL_PREFIX/bin:$PATH"
export RDL2_DSO_PATH="$INSTALL_PREFIX/rdl2dso"
export REZ_MOONRAY_ROOT="$INSTALL_PREFIX"

RC=0
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
echo "=== sha256 ==="
sha256sum "$OUT_EXR" 2>&1
echo "=== exrheader (channels/windows/compression) ==="
"$DEPS_ROOT/bin/exrheader" "$OUT_EXR" 2>&1
echo "=== iinfo -stats (pixel content, not just header validity) ==="
"$DEPS_ROOT/bin/iinfo" -stats "$OUT_EXR" 2>&1
echo "RC_MARKER=$RC"
} > "$RENDER_LOG" 2>&1
cat "$RENDER_LOG"

# The subshell above cannot export RC back out; recover it from the log.
RC=$(sed -n 's/^RC_MARKER=//p' "$RENDER_LOG")

# --- Acceptance gates (each one fails the script, not just the log) ---
[ "$RC" = "0" ]                                   || fail "moonray exited $RC"
[ -s "$OUT_EXR" ]                                 || fail "output EXR missing or empty"
file "$OUT_EXR" | grep -qi "OpenEXR"              || fail "output is not an OpenEXR file"
grep -q "Constant: No"     "$RENDER_LOG"          || fail "image is constant (blank/black render)"
grep -q "^ *Stats NanCount: 0 0 0 0" "$RENDER_LOG" || fail "NaN pixels present"
grep -q "^ *Stats InfCount: 0 0 0 0" "$RENDER_LOG" || fail "Inf pixels present"
grep -qE "512 x +512, 4 channel, float openexr" "$RENDER_LOG" || fail "unexpected image dimensions/format"

echo "PHASE03_RENDER_OK -- $OUT_EXR"
