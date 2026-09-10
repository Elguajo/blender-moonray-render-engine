#!/bin/bash
# Phase 06 -- rebuild moonray_bridge against the Phase 03 installed runtime,
# now including SceneBuilder.cpp (structured CREATE_SCENE/UPDATE_OBJECT/
# UPDATE_CAMERA, see docs/bridge/SCENE_TRANSLATION.md / ADR-0005). Same
# configure/build shape as phase04_build_bridge.sh, kept as a separate build
# directory (bridge06, not bridge04) so Phase 04's evidence build is untouched.
set -euo pipefail

REPO_MNT="${PHASE06_REPO_MNT:-/mnt/d/01_DEV/blender-moonray-render-engine}"
SRC="$REPO_MNT/bridge"
BUILD_DIR=/root/moonray-blender/build/bridge06
INSTALL_PREFIX=/root/moonray-blender/install/openmoonray
DEPS_ROOT=/opt/MoonRay/installs
LOG_DIR=/root/moonray-blender/logs/phase06-build
mkdir -p "$LOG_DIR"

fail() { echo "FAIL: $*" >&2; exit 1; }

case "$(readlink -f "$BUILD_DIR")" in
  /mnt/*) fail "build path $BUILD_DIR resolves under /mnt -- refusing to build there" ;;
esac

test -x "$INSTALL_PREFIX/bin/moonray" || fail "Phase 03 runtime not found at $INSTALL_PREFIX -- build Phase 03 first"

CONFIG_LOG="$LOG_DIR/configure.log"
BUILD_LOG="$LOG_DIR/build.log"

SRC_OPENMOONRAY="${PHASE06_OPENMOONRAY_SRC:-/root/moonray-blender/src/openmoonray}"

echo "=== configuring moonray_bridge (phase06) ==="
export CMAKE_MODULES_ROOT="$SRC_OPENMOONRAY/cmake_modules"
export ISPC="$DEPS_ROOT/bin/ispc"
export CppUnit_ROOT="$DEPS_ROOT"
export JsonCpp_ROOT="$DEPS_ROOT"
export Libcurl_ROOT="$DEPS_ROOT"
export Log4cplus_ROOT="$DEPS_ROOT"
export LUA_DIR="$DEPS_ROOT"
export OpenSubDiv_ROOT="$DEPS_ROOT"
export OpenVDB_ROOT="$DEPS_ROOT"
export Random123_ROOT="$DEPS_ROOT"
export CMAKE_PREFIX_PATH="$DEPS_ROOT:$INSTALL_PREFIX"
cmake -S "$SRC" -B "$BUILD_DIR" \
  -DCMAKE_MODULE_PATH="$CMAKE_MODULES_ROOT/cmake" \
  -DCMAKE_BUILD_TYPE=Release \
  > "$CONFIG_LOG" 2>&1 || { tail -100 "$CONFIG_LOG"; fail "configure failed, see $CONFIG_LOG"; }

echo "=== building moonray_bridge (phase06) ==="
cmake --build "$BUILD_DIR" -- -j "${PHASE06_JOBS:-8}" \
  > "$BUILD_LOG" 2>&1 || { tail -150 "$BUILD_LOG"; fail "build failed, see $BUILD_LOG"; }

test -x "$BUILD_DIR/moonray_bridge" || fail "moonray_bridge binary not produced"
echo "PHASE06_BUILD_OK -- $BUILD_DIR/moonray_bridge"
