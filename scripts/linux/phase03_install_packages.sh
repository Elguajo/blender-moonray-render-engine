#!/bin/bash
# Phase 03 -- install Rocky 9 OS packages required for the MoonRay CPU baseline.
# Runs inside the MoonRay-Rocky9 WSL2 distro, as root. Sources the pinned upstream
# building/Rocky9/install_packages.sh unmodified (do not edit vendored/pinned source),
# with flags chosen for the CPU-only, no-GUI, no-Arras baseline:
#   --nocuda    skip the NVIDIA CUDA repo + cuda-runtime-11-8/cuda-toolkit-11-8 install
#               (GPU/XPU is explicitly out of scope for Phase 03 acceptance)
#   --noqt      skip Qt5 packages (BUILD_QT_APPS=NO -- no moonray_gui/arras_render)
#   --nocgroup  skip libcgroup rpm download+install (only used by Arras distributed
#               rendering nodes, which this project's local single-process CPU baseline
#               does not build or need -- see docs/research/03-upstream-pin-audit.md)
set -eo pipefail
SRC=/root/moonray-blender/src/openmoonray
LOG=/root/moonray-blender/logs/phase03-build/install-packages.log
mkdir -p "$(dirname "$LOG")"
cd "$SRC"
# The pinned upstream script references ${LD_LIBRARY_PATH} unconditionally (line ~87);
# pre-set a default so it doesn't fail under a strict shell that lacks it (nounset is
# deliberately not used here for this reason -- this is our wrapper's concession, the
# vendored script itself is left unmodified).
: "${LD_LIBRARY_PATH:=}"
export LD_LIBRARY_PATH
source building/Rocky9/install_packages.sh --nocuda --noqt --nocgroup 2>&1 | tee "$LOG"
echo "PHASE03_PACKAGES_OK"
