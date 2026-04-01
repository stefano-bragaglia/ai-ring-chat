"""Entry point for AI-Ring-Chat."""

import argparse
import socket
import sys
from dataclasses import dataclass


# Convention: ports below 1024 require elevated privileges
PRIVILEGED_PORT_THRESHOLD = 1024

# Well-known port for the protocol
DEFAULT_PROTOCOL_PORT = 57782

# Default port for test mode (above privileged threshold)
DEFAULT_TEST_PORT = 9000


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
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Does not need to be reachable
        s.connect(("8.8.8.8", 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip


def parse_join_target(target: str, test_mode: bool) -> tuple[str, int]:
    """Parse the --join argument.
    
    Args:
        target: Either 'address:port' or just 'address' (in normal mode),
                or 'address:port' or just 'port' (in test mode)
        test_mode: Whether running in test mode
        
    Returns:
        Tuple of (address, port)
        
    Raises:
        argparse.ArgumentTypeError: If the format is invalid
    """
    if ":" in target:
        # Full address:port format
        parts = target.rsplit(":", 1)
        if len(parts) != 2:
            raise argparse.ArgumentTypeError(
                f"Invalid address:port format: '{target}'"
            )
        address, port_str = parts
        try:
            port = int(port_str)
        except ValueError:
            raise argparse.ArgumentTypeError(
                f"Invalid port in '{target}': '{port_str}' is not a number"
            )
    else:
        # No colon: could be address (normal) or port (test mode)
        if test_mode:
            # Test mode: treat as port, use localhost
            try:
                port = int(target)
            except ValueError:
                raise argparse.ArgumentTypeError(
                    f"Invalid port: '{target}' is not a number"
                )
            address = "127.0.0.1"
        else:
            # Normal mode: treat as address, use default port
            address = target
            port = DEFAULT_PROTOCOL_PORT

    return address, port


def validate_port(port: int, is_test_mode: bool = False) -> None:
    """Validate port number.
    
    Args:
        port: The port number to validate
        is_test_mode: Whether this is for test mode (enforces > 1024)
        
    Raises:
        argparse.ArgumentTypeError: If port is invalid
    """
    if port < 0 or port > 65535:
        raise argparse.ArgumentTypeError(
            f"Port must be between 0 and 65535, got: {port}"
        )
    if is_test_mode and port <= PRIVILEGED_PORT_THRESHOLD:
        raise argparse.ArgumentTypeError(
            f"Test mode port must be greater than {PRIVILEGED_PORT_THRESHOLD} "
            f"(ports below require root privileges)"
        )


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
  %(prog)s --local 9000
  
  # Join an existing ring (normal mode)
  %(prog)s --join 192.168.1.100:57782
  
  # Join an existing ring (test mode)
  %(prog)s --local 9000 --join 127.0.0.1:57782
  %(prog)s --local 9000 --join 9001
  
  # Join using default port (57782)
  %(prog)s --join 192.168.1.100
        """,
    )

    parser.add_argument(
        "-l",
        "--local",
        type=int,
        metavar="PORT",
        help=f"Local test mode port (must be > {PRIVILEGED_PORT_THRESHOLD}; "
             f"uses localhost as address)",
    )

    parser.add_argument(
        "-j",
        "--join",
        metavar="TARGET",
        help="Address:port of node to join. "
             "In normal mode: 'address:port' or 'address' (uses default port 57782). "
             "In test mode: 'address:port' or just 'port' (uses localhost).",
    )

    parsed = parser.parse_args(args)

    # Validate test mode port
    if parsed.local is not None:
        validate_port(parsed.local, is_test_mode=True)
    else:
        # In normal mode, we'll use the auto-detected IP
        pass

    # Parse join target
    is_test_mode = parsed.local is not None
    join_address: str | None = None
    join_port: int | None = None

    if parsed.join is not None:
        join_address, join_port = parse_join_target(parsed.join, is_test_mode)

        # If port was specified as address in normal mode, use default port
        if join_port is None:
            join_port = DEFAULT_PROTOCOL_PORT

        # Validate join port
        validate_port(join_port)

    # Determine local configuration
    if is_test_mode:
        local_address = "127.0.0.1"
        local_port = parsed.local  # type: ignore
    else:
        local_address = get_ipv4_address()
        local_port = DEFAULT_PROTOCOL_PORT

    return NodeConfig(
        address=local_address,
        port=local_port,
        is_test_mode=is_test_mode,
        join_address=join_address,
        join_port=join_port,
    )


def main() -> int:
    """Main entry point.
    
    Returns:
        Exit code (0 for success, non-zero for error)
    """
    config = parse_args()

    print(f"AI-Ring-Chat Node Configuration")
    print(f"{'=' * 40}")
    print(f"Mode:       {'TEST' if config.is_test_mode else 'NORMAL'}")
    print(f"Address:    {config.address}")
    print(f"Port:       {config.port}")
    if config.join_address:
        print(f"Joining:    {config.join_address}:{config.join_port}")
    else:
        print(f"Joining:    (first node - creating new ring)")

    # TODO: Initialize and run the ring chat node
    return 0


if __name__ == "__main__":
    sys.exit(main())
