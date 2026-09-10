#include "SharedMemoryBuffer.h"

#include <fcntl.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <unistd.h>

#include <atomic>
#include <cstdio>
#include <cstring>
#include <stdexcept>

namespace moonray_bridge {

namespace {
std::atomic<unsigned long long> gCounter{0};
}

ShmPublishResult publishToSharedMemory(const std::string& namePrefix, const void* data, std::size_t byteSize)
{
    const unsigned long long seq = gCounter.fetch_add(1);
    const std::string name = namePrefix + "_" + std::to_string(static_cast<long long>(getpid())) + "_" + std::to_string(seq);

    const int fd = shm_open(name.c_str(), O_CREAT | O_EXCL | O_RDWR, 0600);
    if (fd < 0) {
        throw std::runtime_error("shm_open failed for " + name + ": " + std::strerror(errno));
    }
    if (ftruncate(fd, static_cast<off_t>(byteSize)) != 0) {
        const std::string err = std::strerror(errno);
        close(fd);
        shm_unlink(name.c_str());
        throw std::runtime_error("ftruncate failed for " + name + ": " + err);
    }
    void* mapped = mmap(nullptr, byteSize, PROT_WRITE, MAP_SHARED, fd, 0);
    if (mapped == MAP_FAILED) {
        const std::string err = std::strerror(errno);
        close(fd);
        shm_unlink(name.c_str());
        throw std::runtime_error("mmap failed for " + name + ": " + err);
    }
    std::memcpy(mapped, data, byteSize);
    munmap(mapped, byteSize);
    close(fd);

    return ShmPublishResult{name, byteSize};
}

void unlinkSharedMemory(const std::string& name)
{
    if (name.empty()) return;
    if (shm_unlink(name.c_str()) != 0 && errno != ENOENT) {
        std::fprintf(stderr, "moonray_bridge: warning: shm_unlink(%s) failed: %s\n", name.c_str(), std::strerror(errno));
    }
}

} // namespace moonray_bridge
