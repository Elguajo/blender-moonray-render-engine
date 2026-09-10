#!/bin/bash
# Phase 04 -- build moonray_bridge against the Phase 03 installed runtime.
# Runs inside the MoonRay-Rocky9 WSL2 distro. Source lives in the repo (under
# the Windows-mounted /mnt/d path); the build directory itself stays on the
# Linux-native filesystem per the project's "never build under /mnt/*" rule --
# only source is read from /mnt/d, no compiler output is written there.
set -euo pipefail

REPO_MNT="${PHASE04_REPO_MNT:-/mnt/d/01_DEV/blender-moonray-render-engine}"
SRC="$REPO_MNT/bridge"
BUILD_DIR=/root/moonray-blender/build/bridge04
INSTALL_PREFIX=/root/moonray-blender/install/openmoonray
DEPS_ROOT=/opt/MoonRay/installs
LOG_DIR=/root/moonray-blender/logs/phase04-build
mkdir -p "$LOG_DIR"

fail() { echo "FAIL: $*" >&2; exit 1; }

case "$(readlink -f "$BUILD_DIR")" in
  /mnt/*) fail "build path $BUILD_DIR resolves under /mnt -- refusing to build there" ;;
esac

test -x "$INSTALL_PREFIX/bin/moonray" || fail "Phase 03 runtime not found at $INSTALL_PREFIX -- build Phase 03 first"

CONFIG_LOG="$LOG_DIR/configure.log"
BUILD_LOG="$LOG_DIR/build.log"

SRC_OPENMOONRAY="${PHASE04_OPENMOONRAY_SRC:-/root/moonray-blender/src/openmoonray}"

echo "=== configuring moonray_bridge ==="
# Same dependency-hint environment as phase03_build_moonray.sh: SceneRdl2Config's
# own find_dependency() calls (CppUnit, JsonCpp, Log4cplus, Lua, OpenSubdiv,
# OpenVDB, Random123, TBB via ISPC path) resolve through these _ROOT variables,
# not through CMAKE_PREFIX_PATH alone. CMAKE_PREFIX_PATH must be an environment
# variable here, not a -D cache variable: CMake only splits the *environment*
# form on the OS path-list separator (":" on Linux); a -D cache variable
# requires ";" instead.
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

echo "=== building moonray_bridge ==="
cmake --build "$BUILD_DIR" -- -j "${PHASE04_JOBS:-8}" \
  > "$BUILD_LOG" 2>&1 || { tail -150 "$BUILD_LOG"; fail "build failed, see $BUILD_LOG"; }

test -x "$BUILD_DIR/moonray_bridge" || fail "moonray_bridge binary not produced"
echo "PHASE04_BUILD_OK -- $BUILD_DIR/moonray_bridge"
