import socket
import threading
import sys
from textual.app import App, ComposeResult
from textual.containers import Vertical, Horizontal
from textual.widgets import Button, Footer, Header, Input, Static


class ChatClient(App):
    """Chat client with Textual UI for sending and receiving messages."""
    
    CSS_PATH = "node.tcss"  # Add styles here

    def __init__(self, node_name, host='127.0.0.1', port=12345):
        super().__init__()
        self.node_name = node_name
        self.host = host
        self.port = port
        self.client_socket = None
        self.messages = []

    def compose(self) -> ComposeResult:
        CSS_PATH = "node.tcss"
        """Create the UI layout using a grid."""
        yield Header()  # Add header
        yield Footer()  # Add footer

        self.chat_display = Static("", classes="box")  # Area for incoming messages
        self.input_box = Input(placeholder="Type your message here...")  # Input box
        self.send_button = Button(label="Send", id="send_button")  # Send button

        with Vertical(classes="column"):
            yield self.chat_display
            with Horizontal(classes="row"):
                yield self.send_button
                yield self.input_box

    async def on_mount(self):
        """Connect to the server on mount."""
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((self.host, self.port))
        print(f"{self.node_name} connected to server at {self.host}:{self.port}")

        threading.Thread(target=self.listen_for_messages, daemon=True).start()

    def listen_for_messages(self):
        """Listen for incoming messages from the server."""
        while True:
            try:
                message = self.client_socket.recv(1024).decode()
                if message:
                    self.add_message_to_display(message)
                else:
                    break
            except Exception as e:
                print(f"Error: {e}")
                break

    def add_message_to_display(self, message):
        """Update the message display area with new messages."""
        self.messages.append(message)
        message_text = "\n".join(self.messages)
        self.chat_display.update(message_text)

    async def on_button_pressed(self, event: Button.Pressed):
        """Handle the send button press."""
        if event.button.id == "send_button":
            message = self.input_box.value
            if message.strip():
                self.send_message(message)
                self.input_box.value = ""  # Clear the input box

    def send_message(self, message):
        """Send a message to the server."""
        try:
            self.client_socket.send(message.encode())
            self.add_message_to_display(f"{self.node_name}: {message}")
        except Exception as e:
            print(f"Error sending message: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python node.py <node_name>")
        sys.exit(1)

    node_name = sys.argv[1]
    app = ChatClient(node_name)
    app.run()
