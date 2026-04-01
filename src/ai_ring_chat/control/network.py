"""Network utilities for UDP communication."""

import socket

from ai_ring_chat.model.messages import Message, parse_message


def create_socket(port: int) -> socket.socket:
    """Create a UDP socket bound to the specified port.

    Args:
        port: The port number to bind to.

    Returns:
        A configured UDP socket.
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("", port))
    return sock


def send(address: str, port: int, message: Message) -> bool:
    """Send a Message to the specified endpoint.

    Args:
        address: IP address of the destination.
        port: Port number of the destination.
        message: Message object to send.

    Returns:
        True if the message was sent successfully, False otherwise.
    """
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            sock.sendto(str(message).encode(), (address, port))
            return True
        finally:
            sock.close()
    except Exception:
        return False


def receive(sock: socket.socket, timeout: float | None = None) -> Message | None:
    """Receive a message from the socket (non-blocking with timeout).

    Args:
        sock: The socket to receive from.
        timeout: Timeout in seconds (None for blocking).

    Returns:
        Parsed Message object, or None if timeout or error.
    """
    if timeout is not None:
        sock.settimeout(timeout)

    try:
        data, _ = sock.recvfrom(4096)
        msg_str = data.decode()
        return parse_message(msg_str)
    except socket.timeout, OSError, ValueError:
        return None
