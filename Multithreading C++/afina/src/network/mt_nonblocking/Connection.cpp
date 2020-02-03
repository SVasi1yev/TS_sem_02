#include "Connection.h"

#include "unistd.h"
#include <iostream>
#include <sys/uio.h>

namespace Afina {
namespace Network {
namespace MTnonblock {

// See Connection.h
void Connection::Start() {
    std::lock_guard<std::mutex> lock(mu);
    _event.events = MASK_EPOLLRD;
    alive = true;
    server->_logger->debug("Connection created on descriptor {}", _socket);
}

// See Connection.h
void Connection::OnError() {
    std::lock_guard<std::mutex> lock(mu);
    if (alive) {
        alive = false;
        server->_logger->debug("Connection error on descriptor {}", _socket);
    }
}

// See Connection.h
void Connection::OnClose() {
    std::lock_guard<std::mutex> lock(mu);
    if (alive) {
        alive = false;
        server->_logger->debug("Connection on descriptor {} is closed", _socket);
    }
}

// See Connection.h
void Connection::DoRead() {
    std::lock_guard<std::mutex> lock(mu);
    try {
        int new_bytes = -1;
        while ((new_bytes = read(_socket, client_buffer + readed_bytes, sizeof(client_buffer) - readed_bytes)) > 0) {
            readed_bytes += new_bytes;
            server->_logger->debug("Got {} bytes from socket", readed_bytes);

            // Single block of data readed from the socket could trigger inside actions a multiple times,
            // for example:
            // - read#0: [<command1 start>]
            // - read#1: [<command1 end> <argument> <command2> <argument for command 2> <command3> ... ]
            while (readed_bytes > 0) {
                server->_logger->debug("Process {} bytes", readed_bytes);
                // There is no command yet
                if (!command_to_execute) {
                    std::size_t parsed = 0;
                    if (parser.Parse(client_buffer, readed_bytes, parsed)) {
                        // There is no command to be launched, continue to parse input stream
                        // Here we are, current chunk finished some command, process it
                        server->_logger->debug("Found new command: {} in {} bytes", parser.Name(), parsed);
                        command_to_execute = parser.Build(arg_remains);
                        if (arg_remains > 0) {
                            arg_remains += 2;
                        }
                    }

                    // Parsed might fails to consume any bytes from input stream. In real life that could happens,
                    // for example, because we are working with UTF-16 chars and only 1 byte left in stream
                    if (parsed == 0) {
                        break;
                    } else {
                        std::memmove(client_buffer, client_buffer + parsed, readed_bytes - parsed);
                        readed_bytes -= parsed;
                    }
                }

                // There is command, but we still wait for argument to arrive...
                if (command_to_execute && arg_remains > 0) {
                    server->_logger->debug("Fill argument: {} bytes of {}", readed_bytes, arg_remains);
                    // There is some parsed command, and now we are reading argument
                    std::size_t to_read = std::min(arg_remains, std::size_t(readed_bytes));
                    argument_for_command.append(client_buffer, to_read);

                    std::memmove(client_buffer, client_buffer + to_read, readed_bytes - to_read);
                    arg_remains -= to_read;
                    readed_bytes -= to_read;
                }

                // Thre is command & argument - RUN!
                if (command_to_execute && arg_remains == 0) {
                    server->_logger->debug("Start command execution");

                    std::string result;
                    command_to_execute->Execute(*(server->pStorage), argument_for_command, result);

                    // Send response
                    result += "\r\n";
                    {
                        responses.push_back(result);
                        if (!server->run.load()) {
                            _event.events = MASK_EPOLLWR;
                            return;
                        }
                    }

                    // Prepare for the next command
                    command_to_execute.reset();
                    argument_for_command.resize(0);
                    parser.Reset();
                }
            } // while (readed_bytes)
        }

        {
            if (responses.empty()) {
                _event.events = MASK_EPOLLRD;
            } else {
                _event.events = MASK_EPOLLRDWR;
            }
        }
    } catch (std::runtime_error &ex) {
        server->_logger->error("Failed to process connection on descriptor {}: {}", _socket, ex.what());
    }
}

// See Connection.h
void Connection::DoWrite() {
    std::lock_guard<std::mutex> lock(mu);
    assert(responses.size() > 0);
    int ready_responses = resp_buf_size < responses.size() ? resp_buf_size : responses.size();
    struct iovec iovecs[ready_responses];

    for (int i = 0; i < ready_responses; i++) {
        iovecs[i].iov_len = responses[i].size();
        iovecs[i].iov_base = &(responses[i][0]);
    }

    iovecs[0].iov_base = static_cast<char *>(iovecs[0].iov_base) + data_start;
    iovecs[0].iov_len -= data_start;

    int written = writev(_socket, iovecs, ready_responses);

    if (written <= 0) {
        server->_logger->error("Failed to send response");
        if ((errno != EAGAIN) && (written < 0)) {
            OnError();
            return;
        }
        if (server->run.load()) {
            _event.events = MASK_EPOLLRDWR;
        } else {
            _event.events = MASK_EPOLLWR;
        }
        return;
    }
    data_start += written;

    auto it = responses.begin();
    while ((it < responses.end()) && (data_start >= it->size())) {
        data_start -= it->size();
        it++;
    }

    responses.erase(responses.begin(), it);
    if (responses.empty()) {
        if (server->run.load()) {
            _event.events = MASK_EPOLLRD;
        } else {
            OnClose();
        }
    } else {
        if (server->run.load()) {
            _event.events = MASK_EPOLLRDWR;
        } else {
            _event.events = MASK_EPOLLWR;
        }
    }
}

} // namespace MTnonblock
} // namespace Network
} // namespace Afina
