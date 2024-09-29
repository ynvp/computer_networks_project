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
from datetime import datetime


class ServerApp(App):
    """Textual UI for messaging server."""

    CSS_PATH = "server.tcss"  # Add styles here

    def __init__(self, server, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.server = server

    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()

        self.connected_nodes_display = RichLog(
            highlight=True, markup=True, classes="box"
        )
        self.app.connected_nodes_display.write("Address Table  - Connected Nodes: \n")
        self.app.connected_nodes_display.write("laddr = Local Address, raddr = Remote Address\n")
        self.messages_display = RichLog(markup=True, classes="box")
        self.messages_display.write("-------MESSAGES-------")

        self.shutdown_button = Button(label="Shut Down Server", id="shutdown_button")

        with Vertical(classes="column"):
            yield self.connected_nodes_display
            yield self.messages_display
            yield self.shutdown_button

    async def on_mount(self):
        self.title = "Server"
        self.sub_title = "127.0.0.1:8000"

    async def on_button_pressed(self, event: Button.Pressed):
        """Handle shutdown button press."""
        if event.button.id == "shutdown_button":
            self.server.shutdown()
            self.exit()

    def update_messages(self, message):
        """Update message display."""
        self.messages_display.write(message)

    def start_server(self):
        """Start the server in a background thread."""
        threading.Thread(target=self.server.run, daemon=True).start()


class Server(threading.Thread):
    def __init__(self, app, host="127.0.0.1", port=8000):
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
            while self.running:
                try:
                    client_socket, addr = server_socket.accept()
                    node_name = client_socket.recv(1024).decode()
                    self.clients[addr] = (client_socket, node_name)
                    self.app.connected_nodes_display.write(str(client_socket) + " " + node_name)
                    self.broadcast_message(f"Server message: {node_name} connected to server.")
                    threading.Thread(
                        target=self.handle_client, args=(client_socket, addr)
                    ).start()
                except Exception as e:
                    pass

    def handle_client(self, client_socket, addr):
        node_name = self.clients[addr][1]
        while self.running:
            try:
                message = client_socket.recv(1024).decode()
                if not message:
                    break
                self.messages.put((node_name, message))
                self.forward_messages()
                current_time = datetime.now().strftime('%H:%M:%S')
                self.app.update_messages(f"{current_time} - {node_name}: {message}")
            except Exception as e:
                break

        # Handle client disconnection
        self.on_client_disconnect(addr, node_name)

    def on_client_disconnect(self, addr, node_name):
        """Handle client disconnection."""
        del self.clients[addr]  # Remove client from the list
          # Clear the display before displaying all connected nodes
        self.app.connected_nodes_display.clear()
        self.app.connected_nodes_display.write("Address Table  - Connected Nodes: \n")
        self.app.connected_nodes_display.write("laddr = Local Address, raddr = Remote Address\n")
        for (client_socket, name) in self.clients.values():
            self.app.connected_nodes_display.write(
                str(client_socket) + " " + name
            )  # Update display with current clients

        # Inform remaining clients about the disconnection
        self.broadcast_message(f"{node_name} has disconnected.")

    def forward_messages(self):
        while not self.messages.empty():
            node_name, message = self.messages.get()
            current_time = datetime.now().strftime('%H:%M:%S')
            for client_addr, (client_socket, _) in self.clients.items():
                try:
                    client_socket.send(f"{current_time} - {node_name}: {message}".encode())
                except Exception as e:
                    pass

    def broadcast_message(self, message):
        """Send a message to all connected clients."""
        for client_addr, (client_socket, _) in self.clients.items():
            try:
                client_socket.send(message.encode())
            except Exception as e:
                pass

    def shutdown(self):
        self.running = False
        # Inform all clients that the server is shutting down
        self.broadcast_message("SERVER_SHUTDOWN")

        for addr, (client_socket, _) in list(self.clients.items()):
            try:
                client_socket.shutdown(
                    socket.SHUT_RDWR
                )
                client_socket.close()  # Close each client socket
            except Exception as e:
                self.add_message_to_display(f"Error closing connection for {addr}: {e}")


def spawn_node(node_name, host="127.0.0.1", port=8000):
    """Function to spawn a node in a new terminal window."""
    script_path = "Desktop/Assignment1/node.py"  # Path for Mac OS
    if os.name == "nt":  # Windows
        subprocess.Popen(
            ["start", "/max", "cmd", "/K", "python", "node.py", node_name], shell=True
        )
    elif os.uname().sysname == 'Darwin':  # For macOS
        # Open a new Terminal window and run the command with absolute path
        subprocess.Popen(['osascript', '-e',
                          f'tell app "Terminal" to do script "{command}"'])
    else:  # macOS/Linux
        subprocess.Popen(["gnome-terminal", "--", "python", "node.py", node_name])


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
        spawn_node(f"Node{i}", host="127.0.0.1", port=8000)

    # Run the Textual UI
    server_app.run()


if __name__ == "__main__":
    main()
