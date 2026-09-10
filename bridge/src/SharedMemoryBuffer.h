// Bulk framebuffer transport (docs/bridge/FRAMEBUFFER_PROTOCOL.md): publishes a
// contiguous pixel buffer into POSIX shared memory so the client mmaps/reads it
// directly, instead of the control-plane message carrying inline pixel arrays
// (docs/bridge/MESSAGE_SCHEMA.md "Bulk data stays out of the envelope").
#pragma once

#include <cstddef>
#include <string>

namespace moonray_bridge {

struct ShmPublishResult {
    std::string name;  // POSIX shm name, e.g. "/moonray_bridge_fb_1234_0"; readable at /dev/shm<name>
    std::size_t byteSize = 0;
};

// Copies `byteSize` bytes from `data` into a freshly created, uniquely named POSIX
// shared-memory segment and leaves it open (unlinked later via unlinkSharedMemory).
// Throws std::runtime_error on any shm_open/ftruncate/mmap failure.
ShmPublishResult publishToSharedMemory(const std::string& namePrefix, const void* data, std::size_t byteSize);

// Removes a previously published segment. Safe to call on a name that no longer
// exists (logged, not thrown) so bridge shutdown/replacement never crashes on cleanup.
void unlinkSharedMemory(const std::string& name);

} // namespace moonray_bridge
