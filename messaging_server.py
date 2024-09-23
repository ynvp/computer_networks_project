import socket
import threading
import queue
import sys
import subprocess
import os
import signal

class Server(threading.Thread):
    def __init__(self, host='127.0.0.1', port=12345):
        super().__init__()
        self.host = host
        self.port = port
        self.clients = {}
        self.messages = queue.Queue()
        self.running = True

    def run(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            server_socket.bind((self.host, self.port))
            server_socket.listen()
            print(f"Server listening on {self.host}:{self.port}")
            while self.running:
                try:
                    client_socket, addr = server_socket.accept()
                    print(f"Connected by {addr}")
                    threading.Thread(target=self.handle_client, args=(client_socket, addr)).start()
                except Exception as e:
                    print(f"Server error: {e}")

    def handle_client(self, client_socket, addr):
        self.clients[addr] = client_socket
        while self.running:
            try:
                message = client_socket.recv(1024).decode()
                if not message:
                    break
                print(f"Received message from {addr}: {message}")
                self.messages.put((addr, message))
                self.forward_messages()
            except Exception as e:
                print(f"Error: {e}")
                break

        del self.clients[addr]
        client_socket.close()
        print(f"Disconnected {addr}")

    def forward_messages(self):
        while not self.messages.empty():
            addr, message = self.messages.get()
            for client_addr, client_socket in self.clients.items():
                if client_addr != addr:
                    client_socket.send(f"Message from {addr}: {message}".encode())

    def shutdown(self):
        self.running = False
        for addr, client_socket in self.clients.items():
            client_socket.close()  # Close each client socket
        print("All connections closed.")

def spawn_node(node_name, host='127.0.0.1', port=12345):
    """Function to spawn a node in a new terminal window."""
    if os.name == 'nt':  # Windows
        subprocess.Popen(['start', '/max', 'cmd', '/K', 'python', 'node.py', node_name], shell=True)
    else:  # macOS/Linux
        subprocess.Popen(['gnome-terminal', '--', 'python', 'node.py', node_name])

def main():
    if len(sys.argv) < 2:
        print("Usage: python messaging_server.py <number_of_nodes>")
        return

    try:
        number_of_nodes = int(sys.argv[1])
        if number_of_nodes < 2 or number_of_nodes > 255:
            print("Number of nodes must be between 2 and 255.")
            return
    except ValueError:
        print("Please enter a valid number.")
        return

    # Instantiate server
    server = Server()
    server.start()

    # Spawn nodes with names like Node 1, Node 2, etc.
    for i in range(1, number_of_nodes + 1):
        spawn_node(('Node '+ str(i)), host='127.0.0.1', port=12345)

    try:
        # Wait for server shutdown
        server.join()
    except KeyboardInterrupt:
        print("Shutting down the server...")
        server.shutdown()
        server.join()

if __name__ == "__main__":
    main()
