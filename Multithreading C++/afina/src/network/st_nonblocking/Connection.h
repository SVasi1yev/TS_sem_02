#ifndef AFINA_NETWORK_ST_NONBLOCKING_CONNECTION_H
#define AFINA_NETWORK_ST_NONBLOCKING_CONNECTION_H

#include <cstring>

#include "ServerImpl.h"
#include "protocol/Parser.h"
#include <afina/execute/Command.h>
#include <spdlog/logger.h>
#include <sys/epoll.h>
#include <vector>

namespace Afina {
namespace Network {
namespace STnonblock {

class Connection {
public:
    Connection(int s, ServerImpl *server) : _socket(s), server(server) {
        std::memset(&_event, 0, sizeof(struct epoll_event));
        _event.data.ptr = this;
    }

    friend class ServerImpl;

    inline bool isAlive() const { return alive; }

    void Start();

protected:
    void OnError();
    void OnClose();
    void DoRead();
    void DoWrite();

private:
    ServerImpl *server;
    int _socket;
    struct epoll_event _event;
    bool alive;

    std::size_t arg_remains;
    Protocol::Parser parser;
    std::string argument_for_command;
    std::unique_ptr<Execute::Command> command_to_execute;

    std::vector<std::string> responses;
    int data_start = 0;

    static const int MASK_EPOLLRD = EPOLLIN | EPOLLERR | EPOLLRDHUP;
    static const int MASK_EPOLLWR = EPOLLOUT | EPOLLERR | EPOLLRDHUP;
    static const int MASK_EPOLLRDWR = EPOLLIN | EPOLLERR | EPOLLRDHUP | EPOLLOUT;

    static const int resp_buf_size = 64;

    int readed_bytes = 0;
    char client_buffer[4096];
};

} // namespace STnonblock
} // namespace Network
} // namespace Afina

#endif // AFINA_NETWORK_ST_NONBLOCKING_CONNECTION_H
