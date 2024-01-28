#include <string>
#include <unordered_map>
#include <vector>
#include <queue>
#include <uv.h> // Include the libuv header
#include <thread>
#include <condition_variable>
#include <memory>

std::mutex cv_m;
std::mutex resources_mutex;
uv_async_t async; // 添加一个全局的异步处理

struct Client {
    uv_tcp_t handle;
    std::string partial_msg;
    size_t unsent_packets;
    std::queue<std::string> message_queue; // Add a message queue for each client
};

std::unordered_map<uv_stream_t*, std::shared_ptr<Client>> clients;
std::queue<std::string> message_queue;
const size_t MAX_UNSENT_PACKETS = 10000;
const std::string MSG_PREFIX = "AAAA";
bool is_running = true; // Add a global variable to control the infinite loop



void alloc_buffer(uv_handle_t *handle, size_t suggested_size, uv_buf_t *buf) {
    *buf = uv_buf_init((char*) malloc(suggested_size), suggested_size);
}
void echo_write(uv_write_t *req, int status);  // Add this line

void send_client_message(std::shared_ptr<Client> client) {
    if (!client->message_queue.empty() && client->unsent_packets < MAX_UNSENT_PACKETS) {
        std::string message = client->message_queue.front();
        client->message_queue.pop();
        uv_write_t *req = (uv_write_t *) malloc(sizeof(uv_write_t));
        req->data = new std::shared_ptr<Client>(client); // Store a copy of the shared_ptr
        uv_buf_t wrbuf = uv_buf_init((char*)message.c_str(), message.size()); // Use c_str() instead of data()
        uv_write(req, (uv_stream_t*)&client->handle, &wrbuf, 1, echo_write);
        client->unsent_packets++;
    } else {
        fprintf(stderr, "Send message error: message queue is empty or too many unsent packets\n");
    }
}

void echo_write(uv_write_t *req, int status) {
    if (status < 0) {
        fprintf(stderr, "Write error %s\n", uv_err_name(status));
    }
    std::shared_ptr<Client>* client_ptr = (std::shared_ptr<Client>*) req->data;
    std::shared_ptr<Client> client = *client_ptr;
    client->unsent_packets--;
    if (!client->message_queue.empty()) { // Check if there are more messages to send before calling send_client_message
        send_client_message(client);
    }
    delete client_ptr;
    free(req);
}


void async_cb(uv_async_t* handle) { // 异步事件的回调函数
    // 将原来的broadcast_message函数的主体移动到这里
    std::lock_guard<std::mutex> lock(resources_mutex);
    while (!message_queue.empty()) {
        std::string message = message_queue.front();
        message_queue.pop();
        for (auto& pair : clients) {
            std::shared_ptr<Client> client = pair.second;
            client->message_queue.push(message); // Always push to client's queue
            send_client_message(client);
        }
    }
}

void on_close(uv_handle_t* handle) {
    std::lock_guard<std::mutex> lock(resources_mutex);
    clients.erase((uv_stream_t*)handle);
}


void echo_read(uv_stream_t *stream, ssize_t nread, const uv_buf_t *buf) {
    if (nread < 0){
        if (nread != UV_EOF)
            fprintf(stderr, "Read error %s\n", uv_err_name(nread));
        uv_close((uv_handle_t*) stream, on_close);
    } else if (nread > 0) {
        Client* client = (Client*) stream->data;
        client->partial_msg += std::string(buf->base, nread);

        while (client->partial_msg.size() >= 8) {
            if (client->partial_msg.substr(0, 4) != MSG_PREFIX) {
                client->partial_msg = client->partial_msg.substr(1); // Skip one byte
                continue;
            }

            uint32_t msg_len = *(uint32_t*)client->partial_msg.substr(4, 4).data();
            if (client->partial_msg.size() < 8 + msg_len) { // Check if the message is complete
                if (client->partial_msg.size() > 8) { // Check if there is enough data to get the length
                    msg_len = *(uint32_t*)client->partial_msg.substr(4, 4).data();
                    if (client->partial_msg.size() < 8 + msg_len) {
                        break; // If not, break and wait for more data
                    }
                } else {
                    break; // If not, break and wait for more data
                }
            }

            std::string msg = client->partial_msg.substr(8, msg_len);
            client->partial_msg = client->partial_msg.substr(8 + msg_len);

            client->unsent_packets++;
            if (client->unsent_packets >= MAX_UNSENT_PACKETS) {
                uv_close((uv_handle_t*) &client->handle, on_close);
                return;
            }
            uv_async_send(&async); // 发送异步事件
            // Please ensure that the async handler has been properly initialized and started using uv_async_init() and uv_async_start() respectively.
        }
    }

    // Don't forget to free the read buffer
    if (buf->base)
        free(buf->base);
}

void on_new_connection(uv_stream_t *server, int status) {
    if (status < 0) {
        fprintf(stderr, "New connection error %s\n", uv_strerror(status));
        return;
    }

    uv_loop_t *loop = uv_default_loop();

    std::shared_ptr<Client> client = std::make_shared<Client>();
    client->unsent_packets = 0;

    // Initialize the handle before using it
    uv_tcp_t *new_handle = new uv_tcp_t();
    uv_tcp_init(loop, new_handle);
    new_handle->data = client.get();
    client->handle = *new_handle;

    if (uv_accept(server, (uv_stream_t*) new_handle) == 0) {
        uv_read_start((uv_stream_t*) new_handle, alloc_buffer, echo_read);
        std::lock_guard<std::mutex> lock(resources_mutex);
        clients.insert({(uv_stream_t*)new_handle, client});
    } else {
        uv_close((uv_handle_t*) new_handle, NULL);
    }
}



int main() {
    uv_loop_t *loop = uv_default_loop();

    uv_tcp_t server;
    uv_tcp_init(loop, &server);
    uv_async_init(loop, &async, async_cb); // 初始化异步处理

    struct sockaddr_in addr;
    uv_ip4_addr("0.0.0.0", 12345, &addr);

    uv_tcp_bind(&server, (const struct sockaddr*)&addr, 0);
    int r = uv_listen((uv_stream_t*) &server, 128, on_new_connection);
    if (r) {
        fprintf(stderr, "Listen error %s\n", uv_strerror(r));
        return 1;
    }
    int r1 = uv_run(loop, UV_RUN_DEFAULT);
    is_running = false; // Set is_running to false after uv_run returns
    return r1;

}
