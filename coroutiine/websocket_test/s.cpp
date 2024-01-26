#include <iostream>
#include <uv.h>
#include <cstring>

uv_loop_t *loop;
uv_tcp_t server;
std::string partial_msg;

void alloc_buffer(uv_handle_t *handle, size_t suggested_size, uv_buf_t *buf) {
    buf->base = new char[suggested_size];
    buf->len = suggested_size;
}

void echo_write(uv_write_t *req, int status) {
    if (status) {
        fprintf(stderr, "Write error %s\n", uv_strerror(status));
    }
    char *base = (char*) req->data;
    delete base;
    delete req;
}

void echo_read(uv_stream_t *client, ssize_t nread, const uv_buf_t *buf) {
    if (nread < 0) {
        if (nread != UV_EOF)
            fprintf(stderr, "Read error %s\n", uv_err_name(nread));
        uv_close((uv_handle_t*) client, NULL);
    } else if (nread > 0) {
        partial_msg += std::string(buf->base, nread);
        while (partial_msg.size() >= 8) {
            if (partial_msg.substr(0, 4) != "AAAA") {
                partial_msg = partial_msg.substr(1);
                continue;
            }
            uint32_t msg_len = *reinterpret_cast<const uint32_t*>(partial_msg.substr(4, 4).c_str());
            if (partial_msg.size() >= 8 + msg_len) {
                std::string msg = partial_msg.substr(8, msg_len);
                std::cout << "Received data: " << msg << std::endl;
                partial_msg = partial_msg.substr(8 + msg_len);
                uv_write_t *req = new uv_write_t;
                char* data = new char[8 + msg_len];
                memcpy(data, "AAAA", 4);
                memcpy(data + 4, &msg_len, 4);
                memcpy(data + 8, msg.c_str(), msg_len);
                uv_buf_t wrbuf = uv_buf_init(data, 8 + msg_len);
                req->data = (void*) data;
                uv_write(req, client, &wrbuf, 1, echo_write);
            } else {
                break;
            }
        }
    }

    if (buf->base)
        delete buf->base;
}

void on_new_connection(uv_stream_t *server, int status) {
    if (status < 0) {
        fprintf(stderr, "New connection error %s\n", uv_strerror(status));
        return;
    }

    uv_tcp_t *client = new uv_tcp_t;
    uv_tcp_init(loop, client);
    if (uv_accept(server, (uv_stream_t*) client) == 0) {
        uv_read_start((uv_stream_t*) client, alloc_buffer, echo_read);
    }
    else {
        uv_close((uv_handle_t*) client, NULL);
    }
}

int main() {
    loop = uv_default_loop();

    uv_tcp_init(loop, &server);

    struct sockaddr_in addr;
    uv_ip4_addr("0.0.0.0", 12345, &addr);

    uv_tcp_bind(&server, (const struct sockaddr*)&addr, 0);

    int r = uv_listen((uv_stream_t*) &server, 128, on_new_connection);
    if (r) {
        fprintf(stderr, "Listen error %s\n", uv_strerror(r));
        return 1;
    }
    return uv_run(loop, UV_RUN_DEFAULT);
}
