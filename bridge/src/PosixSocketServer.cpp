#include "PosixSocketServer.h"
#include "Protocol.h"

#include <sys/socket.h>
#include <sys/un.h>
#include <unistd.h>

#include <cerrno>
#include <cstring>
#include <stdexcept>

namespace moonray_bridge {

namespace {

void writeAll(int fd, const void* data, std::size_t size)
{
    const char* p = static_cast<const char*>(data);
    std::size_t remaining = size;
    while (remaining > 0) {
        const ssize_t n = ::write(fd, p, remaining);
        if (n < 0) {
            if (errno == EINTR) continue;
            throw std::runtime_error(std::string("write failed: ") + std::strerror(errno));
        }
        p += n;
        remaining -= static_cast<std::size_t>(n);
    }
}

// Returns false only on a clean 0-byte read at the very start of a frame
// (peer disconnected). Any partial-then-EOF is a genuine error.
bool readAll(int fd, void* data, std::size_t size, bool eofAllowedAtStart)
{
    char* p = static_cast<char*>(data);
    std::size_t remaining = size;
    bool first = true;
    while (remaining > 0) {
        const ssize_t n = ::read(fd, p, remaining);
        if (n < 0) {
            if (errno == EINTR) continue;
            throw std::runtime_error(std::string("read failed: ") + std::strerror(errno));
        }
        if (n == 0) {
            if (first && eofAllowedAtStart) return false;
            throw std::runtime_error("peer disconnected mid-frame");
        }
        p += n;
        remaining -= static_cast<std::size_t>(n);
        first = false;
    }
    return true;
}

} // namespace

Connection::~Connection()
{
    if (mFd >= 0) ::close(mFd);
}

Connection::Connection(Connection&& other) noexcept : mFd(other.mFd)
{
    other.mFd = -1;
}

Connection& Connection::operator=(Connection&& other) noexcept
{
    if (this != &other) {
        if (mFd >= 0) ::close(mFd);
        mFd = other.mFd;
        other.mFd = -1;
    }
    return *this;
}

std::optional<std::string> Connection::readFrame()
{
    std::uint32_t lengthLe = 0;
    if (!readAll(mFd, &lengthLe, sizeof(lengthLe), /*eofAllowedAtStart*/ true)) {
        return std::nullopt;
    }
    const std::uint32_t length = lengthLe; // host is little-endian (x86_64)
    if (length == 0 || length > kMaxMessageBytes) {
        throw std::runtime_error("declared frame length " + std::to_string(length) + " is out of bounds");
    }
    std::string body(length, '\0');
    readAll(mFd, body.data(), length, /*eofAllowedAtStart*/ false);
    return body;
}

void Connection::writeFrame(const std::string& body)
{
    const std::uint32_t length = static_cast<std::uint32_t>(body.size());
    writeAll(mFd, &length, sizeof(length));
    writeAll(mFd, body.data(), body.size());
}

PosixSocketServer::PosixSocketServer(const std::string& socketPath) : mSocketPath(socketPath)
{
    mListenFd = ::socket(AF_UNIX, SOCK_STREAM, 0);
    if (mListenFd < 0) {
        throw std::runtime_error(std::string("socket() failed: ") + std::strerror(errno));
    }

    ::unlink(socketPath.c_str()); // remove a stale socket file, ignore ENOENT

    sockaddr_un addr{};
    addr.sun_family = AF_UNIX;
    if (socketPath.size() >= sizeof(addr.sun_path)) {
        throw std::runtime_error("socket path too long for sockaddr_un: " + socketPath);
    }
    std::strncpy(addr.sun_path, socketPath.c_str(), sizeof(addr.sun_path) - 1);

    if (::bind(mListenFd, reinterpret_cast<sockaddr*>(&addr), sizeof(addr)) != 0) {
        throw std::runtime_error(std::string("bind(") + socketPath + ") failed: " + std::strerror(errno));
    }
    if (::listen(mListenFd, /*backlog*/ 1) != 0) {
        throw std::runtime_error(std::string("listen() failed: ") + std::strerror(errno));
    }
}

PosixSocketServer::~PosixSocketServer()
{
    if (mListenFd >= 0) ::close(mListenFd);
    ::unlink(mSocketPath.c_str());
}

Connection PosixSocketServer::accept()
{
    const int fd = ::accept(mListenFd, nullptr, nullptr);
    if (fd < 0) {
        throw std::runtime_error(std::string("accept() failed: ") + std::strerror(errno));
    }
    return Connection(fd);
}

} // namespace moonray_bridge
