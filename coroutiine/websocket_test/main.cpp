#include <websocketpp/config/asio_no_tls.hpp>
#include <websocketpp/server.hpp>
#include <boost/coroutine2/all.hpp>
#include <vector>
#include <atomic>
#include <mutex>
#include <queue>
#include <thread>
#include <iostream>

typedef websocketpp::server<websocketpp::config::asio> server;
server print_server;
std::queue<server::message_ptr> msg_queue; // 用于存储消息的队列
std::atomic<int> queue_size(0); // 用于记录队列大小的原子变量
std::mutex connections_mutex; // 新增一个互斥量，用于保护connections
std::mutex queue_mutex; // 新增一个互斥量，用于保护消息队列

struct weak_ptr_less {
    bool operator()(const std::weak_ptr<void>& a, const std::weak_ptr<void>& b) const {
        return !a.owner_before(b) && !b.owner_before(a);
    }
};

std::vector<websocketpp::connection_hdl> connections;

void handle_open(websocketpp::connection_hdl hdl) {
    std::lock_guard<std::mutex> guard(connections_mutex); // 使用互斥量保护connections
    connections.push_back(hdl);
}

void handle_close(websocketpp::connection_hdl hdl) {
    std::lock_guard<std::mutex> guard(connections_mutex); // 使用互斥量保护connections
    connections.erase(std::remove_if(connections.begin(), connections.end(),
                                     [hdl](const std::weak_ptr<void>& ptr) {
                                         return weak_ptr_less()(ptr, hdl.lock());
                                     }),
                      connections.end());
}

void handle_message(websocketpp::connection_hdl hdl, server::message_ptr msg) {
    std::cout << "handle_message" << std::endl;
    if (queue_size.load() < 100000) { // 如果队列大小小于1000
        std::lock_guard<std::mutex> guard(queue_mutex); // 使用互斥量保护消息队列
        msg_queue.push(msg); // 将消息放入队列
        queue_size.fetch_add(1); // 原子地增加队列大小
    }
}

void run_server(boost::coroutines2::coroutine<void>::push_type& sink) {
    try {
        print_server.set_open_handler(&handle_open);
        print_server.set_close_handler(&handle_close);
        print_server.set_message_handler(&handle_message);
        print_server.init_asio();
        print_server.listen(9002);
        print_server.start_accept();
        print_server.run();·
    } catch (websocketpp::exception const & e) {
        std::cout << e.what() << std::endl;
    } catch (...) {
        std::cout << "An unexpected error occurred." << std::endl;
    }
}

void broadcast_messages(boost::coroutines2::coroutine<void>::push_type& sink) {
    while (true) { // Continuously check the queue in this loop
        std::this_thread::sleep_for(std::chrono::milliseconds(1)); // Add a small delay
        if (!msg_queue.empty()) { // If the queue is not empty
            std::lock_guard<std::mutex> guard(queue_mutex); // Use mutex to protect msg_queue
            auto msg = msg_queue.front(); // Get the message from the queue
            msg_queue.pop(); // Remove the message from the queue
            queue_size.fetch_sub(1); // Decrease the queue size

            // Broadcast the message to all connected clients
            std::lock_guard<std::mutex> guard2(connections_mutex); // Use mutex to protect connections
            for (auto& hdl : connections) {
                print_server.send(hdl, msg->get_payload(), msg->get_opcode());
            }
        }
    }
}

int main() {
    boost::coroutines2::coroutine<void>::pull_type server_coroutine{run_server};
    boost::coroutines2::coroutine<void>::pull_type broadcast_coroutine{broadcast_messages};

    std::thread server_thread([&]() {
        while(server_coroutine) {
            server_coroutine();
        }
    });

    std::thread broadcast_thread([&]() {
        while(broadcast_coroutine) {
            broadcast_coroutine();
        }
    });

    server_thread.join();
    broadcast_thread.join();
    return 0;
}
