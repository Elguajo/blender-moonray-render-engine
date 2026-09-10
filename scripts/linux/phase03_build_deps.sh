#!/bin/bash
# Phase 03 -- build third-party dependencies from source via the pinned upstream
# building/Rocky9/CMakeLists.txt ExternalProject_Add chain (JsonCpp, OpenSubdiv,
# OpenEXR, Random123, ISPC, embree, OpenColorIO, OpenImageIO, TBB, OpenImageDenoise,
# GLFW, OptiXHeaders). Installs into the upstream-default InstallRoot (/opt/MoonRay/installs)
# -- this is Linux-native ext4 (not a Windows mount), and is a hardcoded literal in the
# vendored CMakePresets.json environment block for the main MoonRay build (DEPS_ROOT),
# so relocating it would require editing pinned upstream files. This directory holds
# only a disposable third-party build cache, not MoonRay itself.
#
# -DNO_USD=1: skip building Pixar USD from source. USD/Hydra/hdMoonray is explicitly
# out of scope for Phase 03 (ADR-0002, reference/fallback only) and is never built by
# the separate per-repository moonray builds in phase03_build_moonray.sh, so nothing
# in this project's scope needs it. This also avoids a very large, slow build step.
set -euo pipefail
SRC=/root/moonray-blender/src/openmoonray
BUILD_DEPS=/root/moonray-blender/build-deps
LOG_DIR=/root/moonray-blender/logs/phase03-build
JOBS="${PHASE03_JOBS:-8}"
mkdir -p "$BUILD_DEPS" "$LOG_DIR" /opt/MoonRay/installs/{bin,lib,include}

case "$(readlink -f "$BUILD_DEPS")" in
  /mnt/*) echo "FAIL: build-deps path resolves under /mnt" >&2; exit 1 ;;
esac

LOG="$LOG_DIR/build-deps.log"
cd "$BUILD_DEPS"
echo "=== configuring third-party deps (NO_USD=1) ==="
cmake "$SRC/building/Rocky9" -DNO_USD=1 > "$LOG" 2>&1 || { tail -150 "$LOG"; echo "FAIL: deps configure"; exit 1; }
echo "=== building third-party deps (-j $JOBS, serial ExternalProject chain) ==="
cmake --build . -- -j "$JOBS" >> "$LOG" 2>&1 || { tail -150 "$LOG"; echo "FAIL: deps build"; exit 1; }
echo "PHASE03_DEPS_OK -- log: $LOG"
