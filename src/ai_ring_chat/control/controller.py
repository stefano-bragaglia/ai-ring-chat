"""Controller abstract base class and implementations."""

from abc import ABC, abstractmethod
import threading
import time

from ai_ring_chat.model.nodes import Node
from ai_ring_chat.model.messages import Message, MessageType, Address, format_exit
from ai_ring_chat.view import View
from ai_ring_chat.control import network


class Controller(ABC):
    """Abstract base class for the controller.

    In MVC pattern, the controller coordinates between Model and View.
    """

    @abstractmethod
    def start(self) -> None:
        """Start the controller (begin message handling)."""
        pass

    @abstractmethod
    def stop(self) -> None:
        """Stop the controller."""
        pass


class TkinterController(Controller):
    """Tkinter implementation of the controller.

    Coordinates between Node (Model) and TkinterView (View).
    Handles message receiving loop and PING heartbeat.
    """

    PING_INTERVAL = 2.0  # Seconds between PING messages

    def __init__(self, node: Node, view: View):
        """Initialize the controller.

        Args:
            node: The Node instance (Model)
            view: The View instance (View)
        """
        import socket

        self._node = node
        self._view = view
        self._running = False
        self._ping_thread: threading.Thread | None = None
        self._receive_thread: threading.Thread | None = None
        self._socket: socket.socket | None = None

        # Connect view callbacks
        view.set_send_callback(self.send_message)
        view.set_user_click_callback(self.on_user_click)
        view.set_close_callback(self.on_close)

    def start(self) -> None:
        """Start the controller and message handling."""
        self._running = True
        self._socket = network.create_socket(self._node.port)

        # Start PING thread
        self._ping_thread = threading.Thread(target=self._ping_loop, daemon=True)
        self._ping_thread.start()

        # Start receive thread
        self._receive_thread = threading.Thread(target=self._receive_loop, daemon=True)
        self._receive_thread.start()

    def stop(self) -> None:
        """Stop the controller."""
        self._running = False
        if self._socket:
            self._socket.close()

    def send_message(self) -> None:
        """Send a message from the view input.

        Called when user clicks Send button or presses Enter.
        """
        text = self._view.get_message()
        if not text:
            return

        # Clear input
        self._view.clear_message()

        # Check for private message prefix
        if text.startswith("@"):
            # Parse private message
            parts = text.split(" ", 1)
            if len(parts) >= 2:
                target_str = parts[0][1:]  # Remove @
                payload = parts[1]

                try:
                    target = network.parse_message(f"USER {target_str} payload")
                    if target:
                        # Send private message
                        msg = Message(
                            msg_type=MessageType.USER,
                            sender=Address(self._node.address, self._node.port),
                            content=f"{target_str} {payload}",
                        )
                        self._send_to_next(msg)

                        # Show in our own view
                        self._view.append_message(
                            f"[Private to {target_str}] {payload}"
                        )
                except ValueError, IndexError:
                    pass
        else:
            # Public message
            msg = Message(
                msg_type=MessageType.TEXT,
                sender=Address(self._node.address, self._node.port),
                content=text,
            )
            self._send_to_next(msg)

            # Show in our own view
            self._view.append_message(f"[{self._node.self_address_str}] {text}")

    def on_user_click(self, user_address: str) -> None:
        """Handle user click in the view.

        Args:
            user_address: The clicked user's address:port
        """
        self._view.set_input_text(f"@{user_address} ")

    def on_close(self) -> None:
        """Handle window close - graceful exit."""
        # Send EXIT message
        if self._node.next_address and self._node.next_port:
            exit_msg = format_exit(
                Address(self._node.address, self._node.port),
                Address(self._node.next_address, self._node.next_port),
            )
            msg = network.parse_message(exit_msg)
            if msg:
                self._send_to_next(msg)

        self.stop()

    def handle_message(self, msg: Message) -> None:
        """Handle an incoming message.

        Args:
            msg: The parsed message
        """
        from ai_ring_chat.model.protocol import (
            handle_join,
            handle_exit,
            handle_ping,
            handle_echo,
            handle_next,
            handle_text,
            handle_user,
        )

        # Create send function for protocol handlers
        def send_func(addr: str, port: int, msg_str: str):
            parsed = network.parse_message(msg_str)
            if parsed:
                network.send(addr, port, parsed)

        # Handle based on message type
        match msg.msg_type:
            case MessageType.JOIN:
                handle_join(self._node, msg, send_func)
                self._view.update_user_list(self._node.address_book)
                self._view.append_message(f"Node {msg.sender} joined the ring")

            case MessageType.EXIT:
                handle_exit(self._node, msg, send_func)
                self._view.update_user_list(self._node.address_book)
                self._view.append_message(f"Node {msg.sender} left the ring")

            case MessageType.PING:
                handle_ping(self._node, msg, send_func)

            case MessageType.ECHO:
                handle_echo(self._node, msg, send_func)

            case MessageType.NEXT:
                handle_next(self._node, msg, send_func)
                if self._node.is_head():
                    self._view.append_message("Ring recovery completed")

            case MessageType.TEXT:
                # Add sender to address book
                self._node.add_to_address_book(msg.sender.address, msg.sender.port)
                handle_text(self._node, msg, send_func)
                self._view.append_message(f"[{msg.sender}] {msg.content}")
                self._view.update_user_list(self._node.address_book)

            case MessageType.USER:
                # Add sender to address book
                self._node.add_to_address_book(msg.sender.address, msg.sender.port)
                handle_user(self._node, msg, send_func)
                # If not delivered, it was for someone else
                if (
                    msg.content.split(" ", 1)[0]
                    == f"{self._node.address}:{self._node.port}"
                ):
                    payload = msg.content.split(" ", 1)[1] if " " in msg.content else ""
                    self._view.append_message(f"[Private from {msg.sender}] {payload}")

    def update_user_list(self) -> None:
        """Update the view with current user list."""
        self._view.update_user_list(self._node.address_book)

    def _send_to_next(self, msg: Message) -> bool:
        """Send a message to the next node.

        Args:
            msg: The message to send

        Returns:
            True if sent successfully, False otherwise
        """
        if not self._node.next_address or not self._node.next_port:
            return False
        return network.send(self._node.next_address, self._node.next_port, msg)

    def _ping_loop(self) -> None:
        """Periodically send PING messages to next node."""
        while self._running:
            time.sleep(self.PING_INTERVAL)
            if self._node.next_address and self._node.next_port:
                ping_msg = Message(
                    msg_type=MessageType.PING,
                    sender=Address(self._node.address, self._node.port),
                    content="",
                )
                self._send_to_next(ping_msg)

    def _receive_loop(self) -> None:
        """Receive and process incoming messages."""
        while self._running:
            if self._socket is not None:
                msg = network.receive(self._socket, timeout=1.0)
                if msg:
                    self.handle_message(msg)


# Import Address for use in protocol handlers
