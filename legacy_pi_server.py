# TCP/UDP pi server

import logging, math, random, string, sys, threading, time
from socketserver import (
        BaseRequestHandler, ThreadingTCPServer, ThreadingUDPServer)

HOST, PORT = "0.0.0.0", 31416

def compute_pi():
    error = 0.1 * (random.random() - 0.5)
    pi = str(math.pi + error)
    if random.random() < 0.5:
        ch = random.sample(string.ascii_lowercase + string.ascii_uppercase, 1)[0]
        pos = random.randint(0, len(pi)-1)
        pi = pi[:pos] + ch + pi[pos+1:]
    return pi

def delay():
    time.sleep(0.5)

def tcp_server(host, port):
    class TCPClientHandler(BaseRequestHandler):
        def handle(self):
            logging.info(f"TCP client connected from {self.client_address}")
            delay()
            with self.request as cs:
                cs.sendall(compute_pi().encode())

    server = ThreadingTCPServer((host, port), TCPClientHandler)
    def run_server():
        with server:
            logging.info(f"TCP server started, listening on {(host, port)}")
            server.serve_forever()
            logging.info("TCP server exited")

    threading.Thread(target=run_server).start()
    return server

def udp_server(host, port):
    class UDPClientHandler(BaseRequestHandler):
        def handle(self):
            logging.info(f"UDP client request from {self.client_address}")
            delay()
            _, sock = self.request
            sock.sendto(compute_pi().encode(), self.client_address)

    server = ThreadingUDPServer((host, port), UDPClientHandler)
    def run_server():
        with server:
            logging.info(f"UDP server started, bound to {(host, port)}")
            server.serve_forever()
            logging.info("UDP server exited")

    threading.Thread(target=run_server).start()
    return server

def main():
    logging.basicConfig(level=logging.INFO)
    host = sys.argv[1] if len(sys.argv) > 1 else HOST
    port = int(sys.argv[2]) if len(sys.argv) > 2 else PORT
    servers = (tcp_server(host, port), udp_server(host, port))
    logging.info("Press Ctrl-C to terminate the server")
    try:
        while True:
            time.sleep(1000)
    except:
        pass
    finally:
        logging.info("Exiting")
        for server in servers:
            server.shutdown()

if __name__ == "__main__":
    main()
