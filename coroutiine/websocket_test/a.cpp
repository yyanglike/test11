#include <iostream>
#include <string>
#include <queue>
#include <mutex>
#include <functional>
#include <uv.h>

class TcpClient {
private:
    uv_loop_t* loop = nullptr;
    uv_tcp_t socket;
    uv_connect_t connect_req;

    std::queue<std::string> write_queue;

    bool is_closing = false; // add this line

    std::mutex queue_mutex;
    struct sockaddr_in dest;
    std::function<void(const std::string&)> on_data_received;
    std::string partial_msg; // Used to store part of a message in case of a sticky package

    static void alloc_buffer(uv_handle_t *handle, size_t suggested_size, uv_buf_t *buf) {
        buf->base = (char*) malloc(suggested_size);
        buf->len = suggested_size;
    }

    static void on_read(uv_stream_t *client, ssize_t nread, const uv_buf_t *buf) {
        if (nread < 0) {
            if (nread == UV_EOF) {
                fprintf(stderr, "Server closed the connection\n");
                TcpClient* self = (TcpClient*)client->data;
                if (!self->is_closing) { // check if the connection is closing
                    self->is_closing = true; // set the flag
                    uv_close((uv_handle_t*)client, on_close); // Close the client and reconnect
                }
            } else {
                fprintf(stderr, "Read error %s\n", uv_err_name(nread));
                uv_close((uv_handle_t*)client, NULL);
            }
            free(buf->base);
            return;
        }

        if (nread == 0) {
            // EAGAIN or EWOULDBLOCK
            free(buf->base);
            return;
        }

        std::string data(buf->base, nread);
        TcpClient* self = (TcpClient*)client->data;
        self->partial_msg += data;
        while (self->partial_msg.size() >= 8) { // Check if we have enough data to read the length
            if (self->partial_msg.substr(0, 4) != "AAAA") {
                self->partial_msg = self->partial_msg.substr(1); // Skip one byte
                continue;
            }

            uint32_t msg_len = *(uint32_t*)self->partial_msg.substr(4, 4).c_str();
            if (self->partial_msg.size() >= 8 + msg_len) { // Check if we have a full message
                std::string msg = self->partial_msg.substr(8, msg_len);
                if (self->on_data_received) {
                    self->on_data_received(msg);
                }
                self->partial_msg = self->partial_msg.substr(8 + msg_len); // Remove the message from the buffer
            } else {
                break;
            }
        }
        free(buf->base);
    }

    static void on_connect(uv_connect_t* req, int status) {
        if (status < 0) {
            std::cerr << "Connect error: " << uv_strerror(status) << std::endl;
            TcpClient* client = (TcpClient*)req->data;
            client->reconnect(req);
            return;
        }
        TcpClient* self = (TcpClient*)req->data;
        uv_read_start((uv_stream_t*)&self->socket, alloc_buffer, on_read);
        if (!self->write_queue.empty()) {
            self->write_next();
        }
    }

    static void on_close(uv_handle_t* handle) {
        TcpClient* client = (TcpClient*)handle->data;
        client->is_closing = false; // reset the flag
        uv_tcp_init(client->loop, &client->socket); // initialize the socket
        client->socket.data = client; // add this line
        // Add a delay before reconnecting
        uv_timer_t* timer = (uv_timer_t*)malloc(sizeof(uv_timer_t));
        timer->data = client;
        uv_timer_init(client->loop, timer);
        uv_timer_start(timer, [](uv_timer_t* handle) {
            TcpClient* client = (TcpClient*)handle->data;
            uv_tcp_connect(&client->connect_req, &client->socket, (const struct sockaddr*)&client->dest, on_connect);
            uv_close((uv_handle_t*)handle, [](uv_handle_t* handle) {
                free(handle);
            });
        }, 1000, 0); // Delay for 1 second
    }

    static void on_write(uv_write_t* req, int status) {
        if (status < 0) {
            std::cerr << "Write error: " << uv_strerror(status) << std::endl;
            TcpClient* client = (TcpClient*)req->data;
            client->close((uv_handle_t*)req->handle);
            free(req);
            return;
        }
        TcpClient* client = (TcpClient*)req->data;
        client->write_next_no_lock();
        free(req);
    }

    void reconnect(uv_connect_t* req) {
        TcpClient* client = (TcpClient*)req->data;
        uv_tcp_connect(req, &client->socket, (const struct sockaddr*)&client->dest, on_connect);
    }

    void write_next() {
        std::lock_guard<std::mutex> lock(queue_mutex);
        write_next_no_lock();
    }

    void write_next_no_lock() {
        if (write_queue.empty()) {
            return;
        }

        std::string data = write_queue.front();
        write_queue.pop();

        uint32_t msg_len = data.size();
        std::string msg = "AAAA" + std::string((char*)&msg_len, 4) + data; // Prepend the length to the message

        uv_buf_t buf = uv_buf_init((char*)msg.c_str(), msg.size());
        uv_write_t* req = (uv_write_t*)malloc(sizeof(uv_write_t));
        req->data = this;
        uv_write(req, (uv_stream_t*)&socket, &buf, 1, on_write);
    }

    void close(uv_handle_t* handle) {
        if (!uv_is_closing(handle)) {
            uv_close(handle, on_close);
        }
    }

public:
    uv_loop_t* getLoop() {
        return loop;
    }

public:
    TcpClient(const std::function<void(const std::string&)>& callback) : on_data_received(callback) {
        loop = uv_default_loop();
        uv_tcp_init(loop, &socket);
        socket.data = this;
        connect_req.data = this;
    }

    void connect(const char* ip, int port) {
        uv_ip4_addr(ip, port, &dest);
        uv_tcp_connect(&connect_req, &socket, (const struct sockaddr*)&dest, on_connect);
    }

    void write(const std::string& data) {
        std::lock_guard<std::mutex> lock(queue_mutex);
        write_queue.push(data);

        if (write_queue.size() == 1) {
            write_next_no_lock();
        }
    }

    void run() {
        uv_run(loop, UV_RUN_DEFAULT);
    }
};

int main() {
    TcpClient client([](const std::string& data) {
        // std::cout << "Received data: " << data << std::endl;
    });

    client.connect("127.0.0.1", 12345);
    uv_timer_t timer;
    uv_timer_init(client.getLoop(), &timer);

    timer.data = &client;
    uv_timer_start(&timer, [](uv_timer_t* handle) {
        auto client = static_cast<TcpClient*>(handle->data);
        client->write("Hello, World!");
    }, 1000, 1);
    client.run();

    return 0;
}