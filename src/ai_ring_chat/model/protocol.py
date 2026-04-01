"""Protocol handlers for the ring chat network."""

from ai_ring_chat.model.nodes import Node
from ai_ring_chat.model.messages import Message, MessageType, Address

# Timeout thresholds (in seconds) for head/tail detection
PING_TIMEOUT = 5.0  # If no PING received for this time, node is tail
ECHO_TIMEOUT = 5.0  # If no ECHO received for this time, node is head


def handle_join(node: Node, msg: Message, send_func) -> None:
    """Handle JOIN message.

    Sets node's next to the sender (new node joining),
    adds sender to address book, and propagates JOIN to next.

    Args:
        node: The node receiving the JOIN.
        msg: The JOIN message.
        send_func: Function to send message to next node.
    """
    # Set next to the new node
    node.set_next(msg.sender.address, msg.sender.port)
    # Add sender to address book
    node.add_to_address_book(msg.sender.address, msg.sender.port)
    # Propagate to next
    if node.next_address and node.next_port:
        send_func(node.next_address, node.next_port, str(msg))


def handle_exit(node: Node, msg: Message, send_func) -> None:
    """Handle EXIT message.

    Removes the exiting node from the ring, updates address book,
    and propagates EXIT to next.

    Args:
        node: The node receiving the EXIT.
        msg: The EXIT message (content contains next address).
        send_func: Function to send message to next node.
    """
    # Remove from address book and possibly update next
    _process_exit(node, msg.sender.address, msg.sender.port, msg.content)
    # Propagate to next
    if node.next_address and node.next_port:
        send_func(node.next_address, node.next_port, str(msg))


def _process_exit(
    node: Node, exiting_addr: str, exiting_port: int, content: str
) -> None:
    """Process EXIT: remove from address book and update next if needed."""
    node.remove_from_address_book(exiting_addr, exiting_port)
    # If this node's next is the exiting node, update next
    if node.next_address == exiting_addr and node.next_port == exiting_port and content:
        new_next = Address.parse(content)
        node.set_next(new_next.address, new_next.port)


def handle_ping(node: Node, msg: Message, send_func) -> None:
    """Handle PING message.

    Records the PING timestamp and responds with ECHO.

    Args:
        node: The node receiving the PING.
        msg: The PING message.
        send_func: Function to send message to next node (used for ECHO response).
    """
    # Record that we received a PING
    node.record_ping()
    # Add sender to address book
    node.add_to_address_book(msg.sender.address, msg.sender.port)

    # Send ECHO response back to sender
    response = create_response(node, msg)
    send_func(msg.sender.address, msg.sender.port, str(response))


def handle_echo(node: Node, msg: Message, send_func) -> None:
    """Handle ECHO message.

    Records the ECHO timestamp.

    Args:
        node: The node receiving the ECHO.
        msg: The ECHO message.
        send_func: Function to send message to next node.
    """
    # Record that we received an ECHO
    node.record_echo()
    # Add sender to address book
    node.add_to_address_book(msg.sender.address, msg.sender.port)


def handle_next(node: Node, msg: Message, send_func) -> None:
    """Handle NEXT (recovery) message.

    If node is head (not receiving ECHOs), set next to sender.
    Otherwise, propagate NEXT to next node.

    Args:
        node: The node receiving the NEXT.
        msg: The NEXT message (sender is the tail).
        send_func: Function to send message to next node.
    """
    # Add sender to address book
    node.add_to_address_book(msg.sender.address, msg.sender.port)

    # If node is head, update its next to the sender (tail)
    if node.is_head():
        node.set_next(msg.sender.address, msg.sender.port)
    else:
        # Propagate to next
        if node.next_address and node.next_port:
            send_func(node.next_address, node.next_port, str(msg))


def handle_text(node: Node, msg: Message, send_func) -> None:
    """Handle TEXT (public message).

    Logs the payload, adds sender to address book, and propagates
    if not already in log.

    Args:
        node: The node receiving the TEXT.
        msg: The TEXT message.
        send_func: Function to send message to next node.
    """
    # Add sender to address book
    node.add_to_address_book(msg.sender.address, msg.sender.port)

    # Log the payload
    node.log_payload(msg.content)

    # Propagate if not duplicate (log_payload handles deduplication)
    # Check if message was actually added (not duplicate)
    if msg.content in node.message_log:
        # Propagate to next if not returning to sender
        if node.next_address and node.next_port:
            send_func(node.next_address, node.next_port, str(msg))


def handle_user(node: Node, msg: Message, send_func) -> None:
    """Handle USER (private message).

    Adds sender to address book, delivers to target if this node,
    otherwise propagates.

    Args:
        node: The node receiving the USER.
        msg: The USER message (content has target and payload).
        send_func: Function to send message to next node.
    """
    node.add_to_address_book(msg.sender.address, msg.sender.port)
    target = _extract_target(msg.content)
    if target is None:
        return

    if _is_target_node(node, target):
        node.log_payload(msg.content)
    elif node.next_address and node.next_port:
        send_func(node.next_address, node.next_port, str(msg))


def _extract_target(content: str) -> Address | None:
    """Extract target address from USER message content."""
    parts = content.split(" ", 1)
    if len(parts) < 2:
        return None
    try:
        return Address.parse(parts[0])
    except ValueError:
        return None


def _is_target_node(node: Node, target: Address) -> bool:
    """Check if target matches this node."""
    return target.address == node.address and target.port == node.port


def create_response(node: Node, msg: Message) -> Message:
    """Create a response message.

    Creates an appropriate response based on the received message.
    Currently only handles PING -> ECHO.

    Args:
        node: The node creating the response.
        msg: The original message.

    Returns:
        Response message.
    """
    if msg.msg_type == MessageType.PING:
        return Message(
            msg_type=MessageType.ECHO,
            sender=Address(node.address, node.port),
            content="",
        )
    # Default: return empty response
    return Message(
        msg_type=msg.msg_type,
        sender=Address(node.address, node.port),
        content="",
    )
