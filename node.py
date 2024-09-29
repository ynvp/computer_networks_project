import socket
import threading
import sys
from textual.app import App, ComposeResult
from textual.containers import Vertical, Horizontal
from textual.widgets import Button, Footer, Header, Input, Static, RichLog


class ChatClient(App):
    """Chat client with Textual UI for sending and receiving messages."""

    CSS_PATH = "node.tcss"  # Add styles here

    def __init__(self, node_name, host='127.0.0.1', port=12345):
        super().__init__()
        self.node_name = node_name
        self.host = host
        self.port = port
        self.client_socket = None
        self.running = True  # To keep track of whether the client is running or disconnected
        self.messages = []

    def compose(self) -> ComposeResult:
        """Create the UI layout using a grid."""
        yield Header(node_name)  # Add header
        yield Footer()  # Add footer

        self.chat_display = RichLog(classes="box")  # Area for incoming messages
        self.input_box = Input(placeholder="Type your message here...")  # Input box
        self.send_button = Button(label="Send", id="send_button")  # Send button
        self.disconnect_button = Button(label="Disconnect", id="disconnect_button")  # Disconnect button

        with Vertical(classes="column"):
            yield self.chat_display
            with Horizontal(classes="row"):
                yield self.send_button  # Include the send button
                yield self.disconnect_button  # Include the disconnect button
                yield self.input_box  # Place the input box after the buttons

    async def on_mount(self):
        self.title = self.node_name
        """Connect to the server when the app mounts."""
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.client_socket.connect((self.host, self.port))
        except ConnectionError:
            print(f"Unable to connect to the server at {self.host}:{self.port}")
            return

        # Send node name to the server
        self.client_socket.send(self.node_name.encode())
        print(f"{self.node_name} connected to server at {self.host}:{self.port}")

        # Start a separate thread to listen for incoming messages
        threading.Thread(target=self.listen_for_messages, daemon=True).start()

    def listen_for_messages(self):
        """Listen for incoming messages from the server."""
        while self.running:
            try:
                message = self.client_socket.recv(1024).decode()
                if message:
                    self.add_message_to_display(message)
                else:
                    break
            except Exception as e:
                print(f"Error: {e}")
                break

        self.running = False
        self.client_socket.close()

    def add_message_to_display(self, message):
        """Update the message display area with new messages."""
        self.chat_display.write(message)

    async def on_button_pressed(self, event: Button.Pressed):
        """Handle button presses."""
        if event.button.id == "send_button":
            message = self.input_box.value
            if message.strip():
                self.send_message(message)
                self.input_box.value = ""  # Clear the input box after sending

        elif event.button.id == "disconnect_button":
            self.disconnect_node()

    def send_message(self, message):
        """Send a message to the server."""
        try:
            self.client_socket.send(message.encode())
        except Exception as e:
            print(f"Error sending message: {e}")

    def disconnect_node(self):
        """Gracefully disconnect from the server."""
        if self.client_socket:
            try:
                self.running = False
                self.client_socket.close()
                self.chat_display.write("[Disconnected from server]")
                print(f"{self.node_name} has disconnected from the server.")
            except Exception as e:
                print(f"Error disconnecting: {e}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python node.py <node_name>")
        sys.exit(1)

    node_name = sys.argv[1]
    app = ChatClient(node_name)
    app.run()
