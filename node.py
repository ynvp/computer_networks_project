import socket
import threading
import sys
from textual.app import App, ComposeResult
from textual.containers import Vertical, Horizontal
from textual.widgets import Button, Footer, Header, Input, RichLog


class ChatClient(App):
    """Chat client with Textual UI for sending and receiving messages."""

    CSS_PATH = "node.tcss"  # Add styles here

    def __init__(self, node_name, host="127.0.0.1", port=8000):
        super().__init__()
        self.node_name = node_name
        self.host = host
        self.port = port
        self.client_socket = None
        self.running = True
        self.messages = []

    def compose(self) -> ComposeResult:
        """Create the UI layout using a grid."""
        yield Header(node_name)
        yield Footer()

        self.chat_display = RichLog(classes="box")  # Area for incoming messages
        self.input_box = Input(placeholder="Type your message here...")  # Input box
        self.send_button = Button(label="Send", id="send_button")  # Send button
        self.disconnect_button = Button(
            label="Disconnect", id="disconnect_button"
        )  # Disconnect button

        with Vertical(classes="column"):
            yield self.chat_display
            with Horizontal(classes="row"):
                yield self.send_button
                yield self.disconnect_button
                yield self.input_box

    async def on_mount(self):
        self.title = self.node_name
        """Connect to the server when the app mounts."""
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.client_socket.connect((self.host, self.port))
        except ConnectionError:
            self.add_message_to_display(
                f"Unable to connect to the server at {self.host}:{self.port}"
            )
            return

        # Send node name to the server
        self.client_socket.send(self.node_name.encode())
        self.add_message_to_display(
            f"{self.node_name} connected to server at {self.host}:{self.port}"
        )

        # Start a separate thread to listen for incoming messages
        threading.Thread(target=self.listen_for_messages, daemon=True).start()

    def listen_for_messages(self):
        """Listen for incoming messages from the server."""
        while True:
            try:
                message = self.client_socket.recv(1024).decode()
                if not message:  # Empty message indicates a closed connection
                    break
                if message == "SERVER_SHUTDOWN":
                    self.add_message_to_display("Server: Server is shutting down.")
                    self.close_connection()
                    break
                self.add_message_to_display(message)
            except (ConnectionResetError, OSError) as e:
                self.add_message_to_display(f"Connection error: {e}")
                self.add_message_to_display("System: Connection lost.")
                break

    def add_message_to_display(self, message):
        """Update the message display area with new messages."""
        self.chat_display.write(message)

    async def on_button_pressed(self, event: Button.Pressed):
        """Handle button presses."""
        if event.button.id == "send_button":
            message = self.input_box.value
            if message.strip():
                self.send_message(message)
                self.input_box.value = ""

        elif event.button.id == "disconnect_button":
            self.disconnect_node()

    def send_message(self, message):
        """Send a message to the server."""
        try:
            if self.client_socket is not None:
                self.client_socket.send(message.encode())
            else:
                self.add_message_to_display(
                    "Socket is closed or invalid. Cannot send message."
                )
                self.add_message_to_display(
                    "System: Connection is closed. Cannot send message."
                )
        except (ConnectionResetError, BrokenPipeError, OSError) as e:
            self.add_message_to_display(f"Error sending message: {e}")
            self.add_message_to_display("System: Server is not available.")

    def close_connection(self):
        """Close the client connection gracefully."""
        if self.client_socket:
            try:
                self.client_socket.shutdown(socket.SHUT_RDWR)
                self.client_socket.close()
            except Exception as e:
                self.add_message_to_display(f"Error while closing socket: {e}")
                pass
            finally:
                self.client_socket = None
                self.add_message_to_display("System: Connection closed by the server.")

    def shutdown_client(self):
        """Handle client shutdown."""
        self.close_connection()  # Close the socket first
        self.running = False
        self.add_message_to_display("Client shutdown completed.")

    def disconnect_node(self):
        """Gracefully disconnect from the server."""
        if self.client_socket:
            try:
                self.running = False
                self.client_socket.shutdown(socket.SHUT_RDWR)
                self.client_socket.close()
                self.chat_display.write("[Disconnected from server]")
                self.add_message_to_display(
                    f"{self.node_name} has disconnected from the server."
                )
            except Exception as e:
                self.add_message_to_display(f"Error disconnecting: {e}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python node.py <node_name>")
        sys.exit(1)

    node_name = sys.argv[1]
    app = ChatClient(node_name)
    app.run()
