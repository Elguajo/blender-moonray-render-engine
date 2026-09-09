#!/usr/bin/env bash
set -uo pipefail

BASE="${HOME}/moonray-blender"
BLENDER="${BASE}/tools/blender-current/blender"
LOGDIR="${BASE}/logs"
mkdir -p "${LOGDIR}"
OUT="${LOGDIR}/phase02-host-evidence.txt"
TESTDIR="${BASE}/projects/phase02-smoke"
mkdir -p "${TESTDIR}"
BLEND="${TESTDIR}/phase02-roundtrip.blend"

# Blender exits 0 even when a --python-expr script raises, which would turn a
# failed pxr import or a failed round-trip assertion into a false [PASS].
BPY_STRICT=(--python-exit-code 1)

PASS=0
FAIL=0
WARN=0
pass() { echo "[PASS] $*"; PASS=$((PASS+1)); }
fail() { echo "[FAIL] $*"; FAIL=$((FAIL+1)); }
warn() { echo "[WARN] $*"; WARN=$((WARN+1)); }

run_checks() {

echo "Phase 02 host verification"
date --iso-8601=seconds
echo

echo "=== OS / WSL ==="
cat /etc/os-release
uname -a
echo "WSL_INTEROP=${WSL_INTEROP:-}"
echo "DISPLAY=${DISPLAY:-}"
echo "WAYLAND_DISPLAY=${WAYLAND_DISPLAY:-}"
echo

if grep -qi microsoft /proc/version; then pass "Running under WSL"; else fail "Not running under WSL"; fi
if grep -q 'VERSION_ID="9' /etc/os-release; then pass "Rocky Linux 9.x detected"; else fail "Rocky Linux 9.x not detected"; fi
if [[ -n "${DISPLAY:-}" ]]; then pass "WSLg/X11 DISPLAY is available: ${DISPLAY}"; else fail "DISPLAY is empty"; fi
if [[ -e /dev/dxg ]]; then pass "WSL vGPU device /dev/dxg is present"; else warn "/dev/dxg missing; WSLg GPU acceleration is unavailable"; fi

echo
echo "=== CPU / memory / filesystem ==="
lscpu
free -h
df -h "${HOME}" "${BASE}" 2>/dev/null || true
case "${BASE}" in
  /mnt/*) fail "Build/runtime root is on a Windows-mounted filesystem: ${BASE}" ;;
  *) pass "Build/runtime root is Linux-native: ${BASE}" ;;
esac

echo
echo "=== WSLg graphics ==="
if command -v glxinfo >/dev/null 2>&1; then glxinfo -B || true; else warn "glxinfo is not installed"; fi
if command -v vulkaninfo >/dev/null 2>&1; then vulkaninfo --summary || true; else warn "vulkaninfo is not installed"; fi

# WSLg exposes GPU OpenGL through Mesa's d3d12 Gallium driver on top of
# /usr/lib/wsl/lib/libd3d12.so. Rocky's mesa-dri-drivers package does not ship
# d3d12_dri.so, so GL silently lands on llvmpipe. This does not block the CPU
# render baseline and does not affect the CUDA/OptiX compute path, but it does
# mean the Blender viewport draws in software.
GL_RENDERER="$(glxinfo -B 2>/dev/null | sed -n 's/^OpenGL renderer string: //p')"
if [[ -z "${GL_RENDERER}" ]]; then
  warn "Could not determine the OpenGL renderer string"
elif [[ "${GL_RENDERER}" == *llvmpipe* || "${GL_RENDERER}" == *softpipe* || "${GL_RENDERER}" == *swrast* ]]; then
  warn "OpenGL is software-rendered (${GL_RENDERER}); no d3d12 Gallium driver in $(ls /usr/lib64/dri/d3d12_dri.so 2>/dev/null || echo /usr/lib64/dri)"
else
  pass "OpenGL is hardware-accelerated: ${GL_RENDERER}"
fi

echo
echo "=== NVIDIA / CUDA visibility (non-blocking for CPU baseline) ==="
if command -v nvidia-smi >/dev/null 2>&1; then
  if nvidia-smi; then pass "NVIDIA device is visible in WSL"; else warn "nvidia-smi exists but returned an error"; fi
elif [[ -x /usr/lib/wsl/lib/nvidia-smi ]]; then
  if /usr/lib/wsl/lib/nvidia-smi; then pass "NVIDIA device is visible via /usr/lib/wsl/lib/nvidia-smi"; else warn "WSL nvidia-smi returned an error"; fi
else
  warn "NVIDIA device not detected. CPU baseline can still continue."
fi

echo
echo "=== Blender binary ==="
if [[ ! -x "${BLENDER}" ]]; then
  fail "Blender binary missing: ${BLENDER}"
else
  "${BLENDER}" --version | head -n 12
  if "${BLENDER}" --version | grep -q "Blender 5.2.1"; then pass "Pinned Blender 5.2.1 detected"; else fail "Unexpected Blender version"; fi
fi

echo
echo "=== Blender runtime / bundled Python / USD ==="
PY_EXPR='import bpy,sys,platform; print("BLENDER_VERSION="+bpy.app.version_string); print("PYTHON="+sys.version.replace("\n"," ")); print("PLATFORM="+platform.platform()); import pxr; print("PXR_PACKAGE="+str(pxr.__file__)); from pxr import Usd,Tf; print("USD_VERSION="+str(Usd.GetVersion())); print("TF_MODULE="+str(Tf.__file__))'
if "${BLENDER}" --background --factory-startup "${BPY_STRICT[@]}" --python-expr "${PY_EXPR}"; then
  pass "Blender bundled Python can import pxr/USD"
else
  fail "Blender bundled Python failed pxr/USD identity check"
fi

echo
echo "--- Bundled OpenUSD library identity (Phase 03 ABI input) ---"
# Blender builds OpenUSD under a private namespace; the soname carries it, and
# Phase 03 must link the MoonRay-facing runtime against the same identity.
BLENDER_ROOT="$(dirname "$(readlink -f "${BLENDER}")")"
if find "${BLENDER_ROOT}" -name 'libusd*' -o -name 'libpxr*' 2>/dev/null | head -n 20 | grep -q .; then
  find "${BLENDER_ROOT}" \( -name 'libusd*' -o -name 'libpxr*' \) 2>/dev/null | head -n 20
  pass "Bundled OpenUSD shared libraries located"
else
  warn "No libusd*/libpxr* shared libraries found under ${BLENDER_ROOT}"
fi

echo
echo "=== .blend round-trip ==="
CREATE_EXPR="import bpy; bpy.ops.mesh.primitive_cube_add(); bpy.context.object.name='PHASE02_SMOKE_CUBE'; bpy.ops.wm.save_as_mainfile(filepath=r'${BLEND}'); print('SAVED='+bpy.data.filepath)"
if "${BLENDER}" --background --factory-startup "${BPY_STRICT[@]}" --python-expr "${CREATE_EXPR}" && [[ -s "${BLEND}" ]]; then
  pass "Created smoke-test .blend in Linux-native project path"
else
  fail "Failed to create smoke-test .blend"
fi

OPEN_EXPR="import bpy; assert 'PHASE02_SMOKE_CUBE' in bpy.data.objects; print('ROUNDTRIP_OK='+bpy.data.filepath)"
if "${BLENDER}" --background "${BLEND}" "${BPY_STRICT[@]}" --python-expr "${OPEN_EXPR}"; then
  pass "Reopened .blend and verified object state"
else
  fail "Failed .blend reopen/state verification"
fi

echo
echo "=== Summary ==="
echo "PASS=${PASS}"
echo "WARN=${WARN}"
echo "FAIL=${FAIL}"
echo "EVIDENCE=${OUT}"

if (( FAIL > 0 )); then
  echo "PHASE02_RESULT=FAIL"
  return 1
fi

echo "PHASE02_RESULT=PASS"
return 0
}

# Piping through tee in a subshell (rather than `exec > >(tee ...)`) guarantees
# the evidence file is fully flushed before this script exits.
run_checks 2>&1 | tee "${OUT}"
exit "${PIPESTATUS[0]}"
