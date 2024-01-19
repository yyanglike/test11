#include <websocketpp/config/asio_no_tls.hpp>
#include <websocketpp/server.hpp>
#include <boost/coroutine2/all.hpp>
#include <vector>

typedef websocketpp::server<websocketpp::config::asio> server;
websocketpp::server<websocketpp::config::asio> print_server; // Global variable

struct weak_ptr_less {
    bool operator()(const std::weak_ptr<void>& a, const std::weak_ptr<void>& b) const {
        return !a.owner_before(b) && !b.owner_before(a);
    }
};

std::vector<websocketpp::connection_hdl> connections;

void handle_open(websocketpp::connection_hdl hdl) {
    connections.push_back(hdl);
}

void handle_close(websocketpp::connection_hdl hdl) {
    connections.erase(std::remove_if(connections.begin(), connections.end(),
                                     [hdl](const std::weak_ptr<void>& ptr) {
                                         return weak_ptr_less()(ptr, hdl.lock());
                                     }),
                      connections.end());}

void run_server(boost::coroutines2::coroutine<void>::push_type& sink) {
    try {
        print_server.set_open_handler(&handle_open);
        print_server.set_close_handler(&handle_close);
        print_server.init_asio();
        print_server.listen(9002);
        print_server.start_accept();
        print_server.run();
    } catch (websocketpp::exception const & e) {
        std::cout << e.what() << std::endl;
    }
}


void broadcast_messages(boost::coroutines2::coroutine<void>::push_type& sink) {
    while (true) {
        for (auto hdl : connections) {
            print_server.send(hdl, "Hello, WebSocket!", websocketpp::frame::opcode::text);
        }
        std::this_thread::sleep_for(std::chrono::seconds(1));
    }
}


int main() {
    boost::coroutines2::coroutine<void>::pull_type server_coroutine{run_server};
    boost::coroutines2::coroutine<void>::pull_type broadcast_coroutine{broadcast_messages};
    std::thread server_thread([&]() {
        server_coroutine();
    });
    
    std::thread broadcast_thread([&]() {
        broadcast_coroutine();
    });
    
    server_thread.join();
    broadcast_thread.join();
    return 0;
}
