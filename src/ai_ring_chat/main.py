"""Entry point for AI-Ring-Chat."""

import argparse
import re
import socket
import sys
from dataclasses import dataclass

from ai_ring_chat.model.nodes import Node
from ai_ring_chat.model.messages import Address, format_join
from ai_ring_chat.view.views import TkinterView
from ai_ring_chat.control.controller import TkinterController
from ai_ring_chat.control import network

# Convention: ports below 1024 require elevated privileges
PRIVILEGED_PORT_THRESHOLD = 1024

# Well-known port for the protocol
DEFAULT_PROTOCOL_PORT = 57782

# Regex for valid IPv4 address (each octet 0-255)
IPV4_PATTERN = re.compile(
    r"^(25[0-5]|2[0-4]\d|1?\d\d?)(\.(25[0-5]|2[0-4]\d|1?\d\d?)){3}$"
)


@dataclass
class NodeConfig:
    """Configuration for a ring chat node."""

    address: str
    port: int
    is_test_mode: bool
    join_address: str | None
    join_port: int | None


def get_ipv4_address() -> str:
    """Get the local IPv4 address programmatically.

    Uses an outbound connection to determine the local address.
    Falls back to localhost if detection fails.
    """
    s = None
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Does not need to be reachable
        s.connect(("8.8.8.8", 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        if s is not None:
            s.close()
    return ip


def is_valid_ipv4(address: str) -> bool:
    """Check if a string is a valid IPv4 address.

    Args:
        address: String to check

    Returns:
        True if valid IPv4, False otherwise
    """
    if not IPV4_PATTERN.match(address):
        return False
    # Each octet is already validated by regex (0-255)
    return True


def parse_port(value: str, name: str) -> int:
    """Parse and validate a port number.

    Args:
        value: String representation of port
        name: Name for error messages (e.g., '--self', '--join')

    Returns:
        Valid port number

    Raises:
        argparse.ArgumentTypeError: If port is invalid
    """
    try:
        port = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError(f"Invalid port: '{value}' is not a number")

    if port <= PRIVILEGED_PORT_THRESHOLD or port > 65535:
        raise argparse.ArgumentTypeError(
            f"{name}: port must be between 0 and 65535 and greater than "
            f"{PRIVILEGED_PORT_THRESHOLD} (ports below require root privileges), got {port}"
        )

    return port


def parse_join_target(target: str, is_test_mode: bool) -> tuple[str, int]:
    """Parse the --join argument.

    In test mode: TARGET is just a port number
    In normal mode: TARGET is an IPv4 address (port 57782 is appended)

    Args:
        target: The join target string
        is_test_mode: Whether running in test mode

    Returns:
        Tuple of (address, port)

    Raises:
        argparse.ArgumentTypeError: If the format is invalid
    """
    if is_test_mode:
        # Test mode: target is just a port, address is localhost
        port = parse_port(target, "--join")
        address = "127.0.0.1"
    else:
        # Normal mode: target is an IPv4 address, port is default
        if not is_valid_ipv4(target):
            raise argparse.ArgumentTypeError(
                f"Invalid IPv4 address: '{target}' (expected format: d.d.d.d where d is 0-255)"
            )
        address = target
        port = DEFAULT_PROTOCOL_PORT

    return address, port


def parse_args(args: list[str] | None = None) -> NodeConfig:
    """Parse command line arguments.

    Args:
        args: Arguments to parse (defaults to sys.argv)

    Returns:
        NodeConfig with parsed configuration
    """
    parser = argparse.ArgumentParser(
        prog="ai-ring-chat",
        description="AI-Ring-Chat: A distributed, decentralized UDP chat application "
        "using a ring topology.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Start a new ring (first node)
  %(prog)s
  
  # Join an existing ring (normal mode)
  %(prog)s --join 192.168.1.100
  
  # Test mode with local port
  %(prog)s --self 9000
  
  # Test mode: join another test node
  %(prog)s --self 9000 --join 9001
        """,
    )

    parser.add_argument(
        "-s",
        "--self",
        type=int,
        metavar="PORT",
        help=f"Local test mode port (must be > {PRIVILEGED_PORT_THRESHOLD}; "
        f"uses localhost as address)",
    )

    parser.add_argument(
        "-j",
        "--join",
        metavar="TARGET",
        help="Address to join. "
        "In normal mode: IPv4 address (port 57782 is appended). "
        "In test mode: port number (uses localhost)",
    )

    parsed = parser.parse_args(args)

    # Parse test mode port
    is_test_mode = parsed.self is not None
    local_port: int
    local_address: str

    if is_test_mode:
        # Validate local port
        local_port = parse_port(str(parsed.self), "--self")
        local_address = "127.0.0.1"
    else:
        local_address = get_ipv4_address()
        local_port = DEFAULT_PROTOCOL_PORT

    # Parse join target
    join_address: str | None = None
    join_port: int | None = None

    if parsed.join is not None:
        join_address, join_port = parse_join_target(parsed.join, is_test_mode)

    return NodeConfig(
        address=local_address,
        port=local_port,
        is_test_mode=is_test_mode,
        join_address=join_address,
        join_port=join_port,
    )


def main(args: list[str] | None = None) -> int:
    """Main entry point.

    Args:
        args: Optional list of arguments (defaults to sys.argv)

    Returns:
        Exit code (0 for success, non-zero for error)
    """
    config = parse_args(args)

    print("AI-Ring-Chat Node Configuration")
    print(f"{'=' * 40}")
    print(f"Mode:       {'TEST' if config.is_test_mode else 'NORMAL'}")
    print(f"Address:    {config.address}")
    print(f"Port:       {config.port}")

    # Create the node (Model)
    node = Node(address=config.address, port=config.port)

    # Handle joining an existing ring
    _handle_join(node, config)

    # Create the view and controller
    view = TkinterView(config.address, config.port)
    controller = TkinterController(node, view)

    # Start the controller and view
    controller.start()
    view.show()

    return 0


def _handle_join(node: Node, config) -> None:
    """Handle joining an existing ring.

    Args:
        node: The node to configure
        config: The parsed configuration
    """
    if not config.join_address or not config.join_port:
        print("Joining:    (first node - creating new ring)")
        return

    print(f"Joining:    {config.join_address}:{config.join_port}")

    # Send JOIN message to the target node
    join_msg_str = format_join(Address(config.address, config.port))
    join_msg = network.parse_message(join_msg_str)
    if not join_msg:
        return

    success = network.send(config.join_address, config.join_port, join_msg)
    if not success:
        return

    # Add the target to our address book
    node.add_to_address_book(config.join_address, config.join_port)
    # Set our next to the target (they will set their next to us)
    node.set_next(config.join_address, config.join_port)
    print(f"Sent JOIN to {config.join_address}:{config.join_port}")


if __name__ == "__main__":
    sys.exit(main())
