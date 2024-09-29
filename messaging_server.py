import socket
import threading
import queue
import sys
import os
import subprocess
from textual.app import App, ComposeResult
from textual.containers import Vertical, Horizontal
from textual.widgets import Static, Header, Footer, Button
from textual.widgets import RichLog

class ServerApp(App):
    """Textual UI for messaging server."""
    CSS_PATH = "server.tcss"  # Add styles here

    def __init__(self, server, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.server = server

    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()

        self.status_display = Static("Server Status: Running", classes="box")
        self.connected_nodes_display = RichLog(highlight=True, markup=True, classes="box")
        self.connected_nodes_display.write("Connected Nodes: \n")
        self.messages_display = RichLog(markup=True, classes="box")

        self.shutdown_button = Button(label="Shut Down Server", id="shutdown_button")

        with Vertical(classes="column"):
            yield self.status_display
            yield self.connected_nodes_display
            yield self.messages_display
            yield self.shutdown_button

    async def on_button_pressed(self, event: Button.Pressed):
        """Handle shutdown button press."""
        if event.button.id == "shutdown_button":
            self.status_display.update("Server Status: Shutting Down...")
            self.server.shutdown()
            self.exit()

    def update_messages(self, message):
        """Update message display."""
        self.messages_display.write(message)

    def start_server(self):
        """Start the server in a background thread."""
        threading.Thread(target=self.server.run, daemon=True).start()

class Server(threading.Thread):
    def __init__(self, app, host='127.0.0.1', port=12345):
        super().__init__()
        self.host = host
        self.port = port
        self.clients = {}
        self.messages = queue.Queue()
        self.running = True
        self.app = app

    def run(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            server_socket.bind((self.host, self.port))
            server_socket.listen()
            print(f"Server listening on {self.host}:{self.port}")
            while self.running:
                try:
                    client_socket, addr = server_socket.accept()
                    node_name = client_socket.recv(1024).decode()
                    self.clients[addr] = (client_socket, node_name)
                    self.app.connected_nodes_display.write(node_name)
                    threading.Thread(target=self.handle_client, args=(client_socket, addr)).start()
                except Exception as e:
                    print(f"Server error: {e}")

    def handle_client(self, client_socket, addr):
        node_name = self.clients[addr][1]
        while self.running:
            try:
                message = client_socket.recv(1024).decode()
                if not message:
                    break
                print(f"Received message from {node_name}: {message}")
                self.messages.put((node_name, message))
                self.forward_messages()
                self.app.update_messages(f"{node_name}: {message}")
            except Exception as e:
                print(f"Error: {e}")
                break

        del self.clients[addr]
        client_socket.close()
        self.app.connected_nodes_display.clear()
        self.connected_nodes_display.write("Connected Nodes: \n")
        for (client_socket, node_name) in self.clients.items():
            self.app.connected_nodes_display.write(node_name)

        print(f"Disconnected {node_name} ({addr})")

    def forward_messages(self):
        while not self.messages.empty():
            node_name, message = self.messages.get()
            for client_addr, (client_socket, _) in self.clients.items():
                try:
                    client_socket.send(f"{node_name}: {message}".encode())
                except Exception as e:
                    print(f"Error forwarding message to {client_addr}: {e}")

    def shutdown(self):
        self.running = False
        for addr, (client_socket, _) in self.clients.items():
            client_socket.close()  # Close each client socket


        print("All connections closed.")

def spawn_node(node_name, host='127.0.0.1', port=12345):
    """Function to spawn a node in a new terminal window."""
    if os.name == 'nt':  # Windows
        subprocess.Popen(['start', 'cmd', '/K', 'python', 'node.py', node_name], shell=True)
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

    # Create Textual app and server
    server_app = ServerApp(None)
    server = Server(app=server_app)
    server_app.server = server

    # Start the server and spawn nodes
    server_app.start_server()

    # Spawn nodes with names like Node 1, Node 2, etc.
    for i in range(1, number_of_nodes + 1):
        spawn_node(f'Node {i}', host='127.0.0.1', port=12345)

    # Run the Textual UI
    server_app.run()

if __name__ == "__main__":
    main()
