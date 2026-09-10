// Local-only control-plane transport: a Unix domain socket, one client
// connection at a time (docs/bridge/PROTOCOL.md "no non-local network listener
// by default"; Phase 04 does not need concurrent clients). Wire framing is a
// 4-byte little-endian message length followed by that many bytes of UTF-8 JSON
// (the Envelope from Protocol.h).
#pragma once

#include <cstdint>
#include <optional>
#include <string>

namespace moonray_bridge {

// One accepted client connection. Not copyable; owns its fd.
class Connection {
public:
    explicit Connection(int fd) : mFd(fd) {}
    ~Connection();
    Connection(const Connection&) = delete;
    Connection& operator=(const Connection&) = delete;
    Connection(Connection&& other) noexcept;
    Connection& operator=(Connection&& other) noexcept;

    // Reads one framed message body. Returns std::nullopt on a clean peer
    // disconnect (0-byte read at a frame boundary). Throws std::runtime_error on
    // a socket error, or on a declared frame length that is 0 or exceeds
    // kMaxMessageBytes (framing-level corruption is not resynchronizable, unlike
    // a semantically-malformed-but-well-framed JSON body, which decodeEnvelope
    // handles instead by returning an ERROR while keeping the connection open).
    std::optional<std::string> readFrame();

    // Writes one framed message. Throws std::runtime_error on a socket error,
    // including EPIPE from a peer that already disconnected.
    void writeFrame(const std::string& body);

private:
    int mFd = -1;
};

class PosixSocketServer {
public:
    // Binds and listens on a filesystem Unix-domain-socket path. Removes a
    // stale socket file at that path first (Phase 04 does not implement
    // multi-instance locking; the launcher script is responsible for not
    // running two bridges against the same socket path concurrently).
    explicit PosixSocketServer(const std::string& socketPath);
    ~PosixSocketServer();

    PosixSocketServer(const PosixSocketServer&) = delete;
    PosixSocketServer& operator=(const PosixSocketServer&) = delete;

    // Blocks until a client connects, or throws on accept() failure /
    // interruption by a fatal signal (see main.cpp's shutdown handling).
    Connection accept();

private:
    std::string mSocketPath;
    int mListenFd = -1;
};

} // namespace moonray_bridge
