
#include <stdlib.h>
#include <string.h>
#include <uv.h>
#include <map>
#include <mutex>
#include <string>

#define MAX_CLIENTS 1024
#define MAX_BYTES_PER_SECOND 10240
#define MAX_REQUESTS_PER_SECOND 100

typedef struct {
    uv_write_t req;
    uv_buf_t buf;
} write_req_t;

typedef struct {
    uv_work_t req;
    uv_buf_t buf;
} work_req_t;

typedef struct {
    uv_tcp_t handle;
    std::string partial_msg;
    size_t bytes_received;
    size_t requests_received;
} client_t;

std::map<uv_handle_t*, client_t*> clients;
uv_loop_t *loop;
uv_tcp_t server;
uv_idle_t idler;

void alloc_buffer(uv_handle_t *handle, size_t suggested_size, uv_buf_t *buf) {
    *buf = uv_buf_init((char*) malloc(suggested_size), suggested_size);
}

void free_write_req(uv_write_t *req) {
    write_req_t* wr = (write_req_t*) req;
    free(wr->buf.base);
    free(wr);
}

void on_close(uv_handle_t* handle) {
    clients.erase(handle);
    free(handle);
}

void on_write(uv_write_t *req, int status) {
    if (status) {
        fprintf(stderr, "Write error %s\n", uv_strerror(status));
    }
    free_write_req(req);
}

void after_uv_write(uv_write_t *req, int status) {
    if (status < 0) {
        fprintf(stderr, "uv_write error: %s\n", uv_strerror(status));
    }
    free_write_req(req);
}

void echo_read(uv_work_t *req) {
    // This function will be called in a worker thread.
    // You can do some heavy lifting here.
}

void broadcast_to_clients(const char* data, size_t len) {
    std::string msg(data, len);
    uint32_t msg_len = msg.size();
    for (auto& client : clients) {
        char* final_msg = (char*) malloc(4 + 4 + msg_len);
        memcpy(final_msg, "AAAA", 4);
        memcpy(final_msg + 4, &msg_len, 4);
        memcpy(final_msg + 8, msg.c_str(), msg_len);
        uv_buf_t buf = uv_buf_init(final_msg, msg_len + 8);
        write_req_t *req = (write_req_t*) malloc(sizeof(write_req_t));
        req->buf = buf;
        uv_write(&req->req, (uv_stream_t*)client.second, &req->buf, 1, after_uv_write);
    }
    // Now, each client gets its own copy of the message, which is freed after it is sent.
}

void after_work(uv_work_t *req, int status) {
    // Lock the access to the server and clients here to prevent data race
    static std::mutex mtx;
    std::lock_guard<std::mutex> lock(mtx);

    work_req_t *work_req = (work_req_t*) req;
    free(work_req->buf.base);
    free(work_req);
}

void after_uv_read(uv_stream_t *client, ssize_t nread, const uv_buf_t *buf) {
    client_t* client_info = clients[(uv_handle_t*)client];
    if (nread < 0) {
        if (nread != UV_EOF)
            fprintf(stderr, "Read error %s\n", uv_err_name(nread));
        uv_close((uv_handle_t*) client, on_close);
        free(buf->base);
        return;
    }

    // Check if client is exceeding the limit
    if (++client_info->requests_received > MAX_REQUESTS_PER_SECOND ||
        (client_info->bytes_received += nread) > MAX_BYTES_PER_SECOND) {
        uv_close((uv_handle_t*) client, on_close);
        free(buf->base);
        return;
    }

    std::string data(buf->base, nread);
    client_info->partial_msg += data;
    while (client_info->partial_msg.size() >= 8) { // Check if we have enough data to read the length
        if (client_info->partial_msg.substr(0, 4) != "AAAA") {
            client_info->partial_msg = client_info->partial_msg.substr(1); // Skip one byte
            continue;
        }

        uint32_t msg_len;
        memcpy(&msg_len, client_info->partial_msg.substr(4, 4).c_str(), 4);
        if (client_info->partial_msg.size() >= 8 + msg_len) { // Check if we have a full message

        /*
            我们首先定义了一个工作请求和数据结构，然后定义了两个函数：一个在工作线程中运行，另一个在主线程中运行。
            然后我们创建了一个工作请求，将它加入到libuv的工作队列中。当libuv有空闲的工作线程时，它会调用我们定义的process_msg_work函数。
            当这个函数完成时，libuv会在主线程中调用我们定义的after_process_msg函数。
            // 定义一个工作请求和数据结构
            struct work_req_data {
                uv_work_t req;
                std::string msg;
            };

            // 定义一个在工作线程中运行的函数
            void process_msg_work(uv_work_t* req) {
                work_req_data* data = static_cast<work_req_data*>(req->data);
                process_msg(data->msg);
            }

            // 定义一个在主线程中运行的函数
            void after_process_msg(uv_work_t* req, int status) {
                // 这里可以处理工作线程完成后的事情，比如清理资源
                delete req;
            }

            // 在你的代码中
            std::string msg = client_info->partial_msg.substr(8, msg_len);
            broadcast_to_clients(msg.c_str(), msg.size());

            // 创建一个工作请求
            work_req_data* data = new work_req_data;
            data->req.data = data;
            data->msg = msg;

            // 将工作请求加入到libuv的工作队列中
            uv_queue_work(uv_default_loop(), &data->req, process_msg_work, after_process_msg);
        
        */
            std::string msg = client_info->partial_msg.substr(8, msg_len);
            broadcast_to_clients(msg.c_str(), msg.size());
            client_info->partial_msg = client_info->partial_msg.substr(8 + msg_len); // Remove the processed message
        } else {
            break;
        }
    }

    work_req_t *work_req = (work_req_t*) malloc(sizeof(work_req_t));
    work_req->buf = uv_buf_init(buf->base, nread);
    uv_queue_work(loop, &work_req->req, echo_read, after_work);
}


void on_new_connection(uv_stream_t *server, int status) {
    if (status < 0) {
        fprintf(stderr, "New connection error %s\n", uv_strerror(status));
        return;
    }

    client_t *client = (client_t*) malloc(sizeof(client_t));
    uv_tcp_init(loop, &client->handle);
    if (uv_accept(server, (uv_stream_t*) client) == 0) {
        uv_read_start((uv_stream_t*) client, alloc_buffer, after_uv_read);
        clients[(uv_handle_t*)client] = client;
    }
    else {
        uv_close((uv_handle_t*) client, on_close);
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
