#!/usr/bin/env bash
set -euo pipefail

BLENDER_VERSION="5.2.1"
BLENDER_SERIES="Blender5.2"
BASE="${HOME}/moonray-blender"
CACHE="${BASE}/cache"
TOOLS="${BASE}/tools"
BLENDER_DIR="${TOOLS}/blender-${BLENDER_VERSION}"
BLENDER_LINK="${TOOLS}/blender-current"
LOGS="${BASE}/logs"
PROJECTS="${BASE}/projects"
SRC="${BASE}/src"
BUILD="${BASE}/build"
INSTALL="${BASE}/install"

echo "==> Phase 02 Linux host bootstrap"

if ! grep -qi microsoft /proc/version; then
  echo "ERROR: this script is intended to run inside WSL2." >&2
  exit 1
fi

if [[ ! -r /etc/rocky-release ]]; then
  echo "ERROR: Rocky Linux was not detected." >&2
  exit 1
fi

# The Rocky WSL base image logs in as root and may ship without sudo.
if [[ "$(id -u)" -eq 0 ]]; then
  SUDO=""
elif command -v sudo >/dev/null 2>&1; then
  SUDO="sudo"
else
  echo "ERROR: not root and sudo is unavailable." >&2
  exit 1
fi

# Core toolchain/runtime packages. A failure here is a real blocker.
CORE_PACKAGES=(
  curl wget ca-certificates tar xz git
  gcc gcc-c++ make cmake
  python3 python3-pip
  libX11 libXi libXcursor libXrandr libXinerama libXxf86vm
  libxkbcommon dbus-libs
  mesa-libGL mesa-libEGL mesa-dri-drivers
)

# Diagnostic/graphics extras. Availability varies by repo set (AppStream/CRB),
# and a missing one must not abort the whole host bootstrap: the verifier
# reports each of them as a non-blocking WARN instead.
OPTIONAL_PACKAGES=(
  git-lfs ninja-build
  mesa-vulkan-drivers vulkan-loader vulkan-tools
  glx-utils
)

echo "==> Update packages"
${SUDO} dnf -y update

echo "==> Install core host/runtime packages"
${SUDO} dnf -y install "${CORE_PACKAGES[@]}"

echo "==> Install optional graphics/diagnostic packages (non-blocking)"
MISSING_OPTIONAL=()
for pkg in "${OPTIONAL_PACKAGES[@]}"; do
  if ${SUDO} dnf -y install "${pkg}"; then
    echo "    installed: ${pkg}"
  else
    echo "    WARN: optional package unavailable: ${pkg}"
    MISSING_OPTIONAL+=("${pkg}")
  fi
done

echo "==> Create Linux-native production layout"
mkdir -p \
  "${CACHE}" "${TOOLS}" "${LOGS}" "${PROJECTS}" \
  "${SRC}" "${BUILD}" "${INSTALL}" "${BASE}/tmp"

BLENDER_ARCHIVE="blender-${BLENDER_VERSION}-linux-x64.tar.xz"
BLENDER_URL="https://download.blender.org/release/${BLENDER_SERIES}/${BLENDER_ARCHIVE}"
BLENDER_SHA_URL="https://download.blender.org/release/${BLENDER_SERIES}/blender-${BLENDER_VERSION}.sha256"
ARCHIVE_PATH="${CACHE}/${BLENDER_ARCHIVE}"
SHA_PATH="${CACHE}/blender-${BLENDER_VERSION}.sha256"

echo "==> Download Blender ${BLENDER_VERSION} LTS and official SHA256 list"
if [[ ! -f "${ARCHIVE_PATH}" ]]; then
  curl -fL --retry 3 "${BLENDER_URL}" -o "${ARCHIVE_PATH}"
fi
curl -fL --retry 3 "${BLENDER_SHA_URL}" -o "${SHA_PATH}"

EXPECTED="$(grep -F " ${BLENDER_ARCHIVE}" "${SHA_PATH}" | awk '{print $1}' | head -n1)"
if [[ -z "${EXPECTED}" ]]; then
  echo "ERROR: Blender SHA256 entry not found." >&2
  exit 1
fi
ACTUAL="$(sha256sum "${ARCHIVE_PATH}" | awk '{print $1}')"

echo "Blender SHA256 expected: ${EXPECTED}"
echo "Blender SHA256 actual:   ${ACTUAL}"
[[ "${EXPECTED}" == "${ACTUAL}" ]] || { echo "ERROR: Blender archive checksum mismatch." >&2; exit 1; }

echo "==> Install pinned Blender build"
rm -rf "${BLENDER_DIR}"
tar -xJf "${ARCHIVE_PATH}" -C "${TOOLS}"
mv "${TOOLS}/blender-${BLENDER_VERSION}-linux-x64" "${BLENDER_DIR}"
ln -sfn "${BLENDER_DIR}" "${BLENDER_LINK}"

mkdir -p "${HOME}/bin"
cat > "${HOME}/bin/blender-moonray-host" <<LAUNCHER
#!/usr/bin/env bash
# Phase 02 production baseline: force X11 through WSLg first.
# Blender 5.2 supports Wayland too; test it later as a separate variable.
export WAYLAND_DISPLAY=""
exec "${BLENDER_LINK}/blender" "\$@"
LAUNCHER
chmod +x "${HOME}/bin/blender-moonray-host"

if ! grep -q 'export PATH="$HOME/bin:$PATH"' "${HOME}/.bashrc" 2>/dev/null; then
  printf '\nexport PATH="$HOME/bin:$PATH"\n' >> "${HOME}/.bashrc"
fi

echo "==> Blender CLI sanity check"
"${BLENDER_LINK}/blender" --version | head -n 8

echo
echo "Bootstrap completed."
echo "Linux root: ${BASE}"
echo "Blender:    ${BLENDER_LINK}/blender"
echo "Launcher:   ${HOME}/bin/blender-moonray-host"
if (( ${#MISSING_OPTIONAL[@]} > 0 )); then
  echo "Optional packages NOT installed: ${MISSING_OPTIONAL[*]}"
fi
echo
echo "Next command:"
echo "  bash scripts/linux/phase02_verify_host.sh"
