# moonray_bridge -- Phase 04 prototype native process.
# See docs/phases/04-direct-bridge-prototype.md and docs/bridge/PROTOCOL.md.
#
# Build against the Phase 03 installed runtime, e.g.:
#   cmake -S bridge -B /root/moonray-blender/build/bridge \
#     -DCMAKE_PREFIX_PATH="/opt/MoonRay/installs:/root/moonray-blender/install/openmoonray" \
#     -DCMAKE_BUILD_TYPE=Release
#   cmake --build /root/moonray-blender/build/bridge
# (never configure/build under /mnt/*; see scripts/linux/phase04_build_bridge.sh)
cmake_minimum_required(VERSION 3.23.1)
project(moonray_bridge LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

find_package(SceneRdl2 REQUIRED)
find_package(Moonray REQUIRED)

add_executable(moonray_bridge
    src/main.cpp
    src/Protocol.cpp
    src/PosixSocketServer.cpp
    src/RenderSession.cpp
    src/SharedMemoryBuffer.cpp
)

# MoonRay's exported CMake targets do not propagate the ISA compile flags the
# MoonRay build itself requires (docs/evidence/phase04/build.log records the
# avxintrin.h failure without this, discovered during Phase 04 build prep).
# MoonRay sets these via cmake_modules/cmake/MoonrayDso.cmake; any downstream
# translation unit that includes MoonRay headers needs the same flags.
target_compile_options(moonray_bridge PRIVATE -march=core-avx2 -mavx)

target_link_libraries(moonray_bridge PRIVATE
    Moonray::rendering_rndr
    SceneRdl2::scene_rdl2
    JsonCpp::JsonCpp
    rt
)
