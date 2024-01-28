#include <stdio.h>
#include <stdlib.h>
#include <uv.h>
#include <string>
#include <mutex>


typedef struct {
    uv_tcp_t handle;
    std::string partial_msg;
} client_t;

uv_loop_t *loop;
uv_tcp_t server;
uv_idle_t idler;
client_t* clients[1024];
int client_count = 0;

typedef struct {
    uv_write_t req;
    uv_buf_t buf;
} write_req_t;

typedef struct {
    uv_work_t req;
    uv_buf_t buf;
} work_req_t;

void alloc_buffer(uv_handle_t *handle, size_t suggested_size, uv_buf_t *buf) {
    *buf = uv_buf_init((char*) malloc(suggested_size), suggested_size);
}

void idle_cb(uv_idle_t* handle) {
    // This function will be called by libuv when there are no other tasks to perform.
    // You can do some cleanup or status update here.
}

void free_write_req(uv_write_t *req) {
    write_req_t* wr = (write_req_t*) req;
    free(wr->buf.base);
    free(wr);
}

void on_close(uv_handle_t* handle) {
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
    for (int i = 0; i < client_count; i++) {
        char* final_msg = (char*) malloc(4 + 4 + msg_len);
        memcpy(final_msg, "AAAA", 4);
        memcpy(final_msg + 4, &msg_len, 4);
        memcpy(final_msg + 8, msg.c_str(), msg_len);
        uv_buf_t buf = uv_buf_init(final_msg, msg_len + 8);
        write_req_t *req = (write_req_t*) malloc(sizeof(write_req_t));
        req->buf = buf;
        uv_write(&req->req, (uv_stream_t*)clients[i], &req->buf, 1, after_uv_write);
    }
    // Now, each client gets its own copy of the message, which is freed after it is sent.
}


/*

uv_queue_work 是libuv库中的一个函数，它的作用是将一些耗时的任务放到一个单独的线程中进行处理，不阻塞主线程的执行。这样可以提高程序的性能，特别是在处理一些I/O密集型或者CPU密集型的任务时。

这个函数接受四个参数：事件循环、工作请求、工作函数和完成回调函数。工作函数会在一个单独的线程中运行，完成后在主线程中调用完成回调函数。

这样的设计模式使得libuv可以在单线程中高效地处理大量的并发请求，同时也可以充分利用多核CPU的计算能力。
*/
void after_work(uv_work_t *req, int status) {
    // Lock the access to the server and clients here to prevent data race
    static std::mutex mtx;
    std::lock_guard<std::mutex> lock(mtx);

    work_req_t *work_req = (work_req_t*) req;
    // write_req_t *write_req = (write_req_t*) malloc(sizeof(write_req_t));
    // write_req->buf = work_req->buf;
    // uv_write(&write_req->req, (uv_stream_t*)&server, &write_req->buf, 1, after_uv_write);
    // broadcast_to_clients(work_req->buf.base, work_req->buf.len);
    free(work_req);
}

void after_uv_read(uv_stream_t *client, ssize_t nread, const uv_buf_t *buf) {
    client_t* client_info = (client_t*) client;
    if (nread < 0) {
        if (nread != UV_EOF)
            fprintf(stderr, "Read error %s\n", uv_err_name(nread));
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
        // fprintf(stderr, "messagelength: %d\n", msg_len);
        if (client_info->partial_msg.size() >= 8 + msg_len) { // Check if we have a full message
            std::string msg = client_info->partial_msg.substr(8, msg_len);
            // Here you can process the message, for example, broadcast it to other clients
            broadcast_to_clients(msg.c_str(), msg.size());
            client_info->partial_msg = client_info->partial_msg.substr(8 + msg_len); // Remove the processed message
            //
        } else {
            // If we don't have a full message, we break the loop and wait for more data to arrive
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
        clients[client_count++] = client;
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
    uv_idle_init(loop, &idler);
    uv_idle_start(&idler, idle_cb);
    return uv_run(loop, UV_RUN_DEFAULT);
}
