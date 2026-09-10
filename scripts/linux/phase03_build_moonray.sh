#!/bin/bash
# Phase 03 -- reproducible native MoonRay CPU-baseline build.
# Runs inside the MoonRay-Rocky9 WSL2 distro. Never run against a /mnt/* path.
#
# Builds cmake_modules (source-only), scene_rdl2, mcrt_denoise, moonray, moonshine
# as SEPARATE per-repository CMake projects (per openmoonray/building/general_build.md,
# "Building the Repositories Separately"), NOT via the openmoonray superproject's own
# top-level CMakeLists.txt / rocky9-release preset.
#
# Reason: openmoonray/CMakeLists.txt and moonray/CMakeLists.txt call add_subdirectory()
# unconditionally on rats, arras/arras4_core, arras/distributed, hydra, moonray_arras,
# moonray_dcc_plugins, moonshine_usd and render_profile_viewer -- none of which are
# initialized (out of scope: Hydra/hdMoonray, Arras distributed rendering, USD). The
# monolithic superproject configure would either hard-fail (uninitialized submodule has
# no CMakeLists.txt) or, if those submodules were initialized just to satisfy the
# directory walk, would drag in the full USD/Hydra/Arras dependency chain this phase
# must not touch. Building each required repository separately avoids both problems and
# is an upstream-documented, supported path.
#
# Fail-fast, idempotent (each install step is a plain `cmake --install`, safe to re-run),
# pinned to the exact commits in configs/moonray-source-lock.json, logs every step.

set -euo pipefail

SRC=/root/moonray-blender/src/openmoonray
BUILD_ROOT=/root/moonray-blender/build
INSTALL_PREFIX=/root/moonray-blender/install/openmoonray
DEPS_ROOT=/opt/MoonRay/installs
LOG_DIR=/root/moonray-blender/logs/phase03-build
JOBS="${PHASE03_JOBS:-8}"

mkdir -p "$LOG_DIR" "$BUILD_ROOT" "$INSTALL_PREFIX"

fail() { echo "FAIL: $*" >&2; exit 1; }

# --- Safety: never build on a Windows-mounted filesystem ---
case "$(readlink -f "$SRC")" in
  /mnt/*) fail "source path $SRC resolves under /mnt -- refusing to build on a Windows-mounted filesystem" ;;
esac
case "$(readlink -f "$BUILD_ROOT")" in
  /mnt/*) fail "build path $BUILD_ROOT resolves under /mnt -- refusing to build on a Windows-mounted filesystem" ;;
esac

# --- Safety: re-verify pinned submodule SHAs before touching anything ---
declare -A EXPECT=(
  [cmake_modules]=1b1b7af8111b0a8ceaff45f3c47a778b0ca07ec4
  [moonray/scene_rdl2]=1229d3eaa1ee41dc1ddefbe781c623edceafbac8
  [moonray/mcrt_denoise]=0050e726309a533e7964bd05380430e6b06cce7a
  [moonray/moonray]=eef67ae992b5037943a7716cca96ed443c36dcec
  [moonray/moonshine]=a3c8667298a23df7d6efed128cb475484de66c8e
)
for path in "${!EXPECT[@]}"; do
  actual=$(git -C "$SRC/$path" rev-parse HEAD)
  [ "$actual" = "${EXPECT[$path]}" ] || fail "pin mismatch on $path: expected ${EXPECT[$path]}, got $actual -- STOP, do not build"
done
echo "Pin verification OK for all 5 required components."

# --- Common environment (per building/general_build.md "Finding Dependencies") ---
export CMAKE_MODULES_ROOT="$SRC/cmake_modules"
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
export PATH="$INSTALL_PREFIX/bin:$PATH"

build_repo() {
  local name="$1" src_subdir="$2"
  local build_dir="$BUILD_ROOT/$name"
  local log="$LOG_DIR/build-$name.log"
  echo "=== configuring $name ==="
  cmake -S "$SRC/$src_subdir" -B "$build_dir" \
    -DCMAKE_MODULE_PATH="$CMAKE_MODULES_ROOT/cmake" \
    -DPYTHON_EXECUTABLE=python3 \
    -DBOOST_PYTHON_COMPONENT_NAME=python39 \
    -DABI_VERSION=0 \
    -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_INSTALL_PREFIX="$INSTALL_PREFIX" \
    -DMOONRAY_USE_OPTIX=NO \
    "${@:3}" \
    > "$log" 2>&1 || { tail -100 "$log"; fail "$name configure failed, see $log"; }
  echo "=== building $name (-j $JOBS) ==="
  cmake --build "$build_dir" -- -j "$JOBS" >> "$log" 2>&1 || { tail -100 "$log"; fail "$name build failed, see $log"; }
  echo "=== installing $name ==="
  cmake --install "$build_dir" >> "$log" 2>&1 || { tail -100 "$log"; fail "$name install failed, see $log"; }
  echo "$name OK -- log: $log"
}

build_repo scene_rdl2   moonray/scene_rdl2
build_repo mcrt_denoise moonray/mcrt_denoise
build_repo moonray      moonray/moonray
build_repo moonshine    moonray/moonshine

echo "PHASE03_BUILD_OK"
