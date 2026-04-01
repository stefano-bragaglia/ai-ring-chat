"""Node data model for the ring chat protocol."""

from dataclasses import dataclass, field


@dataclass
class Node:
    """Represents a node in the ring chat network.

    Attributes:
        address: The IP address of this node.
        port: The port number of this node.
        next_address: The IP address of the next node in the ring (None if single node).
        next_port: The port number of the next node in the ring (None if single node).
        address_book: Sorted list of known addresses in the ring (alphabetical order).
        message_log: List of recent message payloads for deduplication.
    """

    address: str
    port: int
    next_address: str | None = None
    next_port: int | None = None
    address_book: list[str] = field(default_factory=list)
    message_log: list[str] = field(default_factory=list)

    def set_next(self, address: str, port: int) -> None:
        """Set the next node in the ring.

        Args:
            address: IP address of the next node.
            port: Port number of the next node.
        """
        self.next_address = address
        self.next_port = port

    def remove_next(self) -> None:
        """Remove the next node from the ring (set to None)."""
        self.next_address = None
        self.next_port = None

    def add_to_address_book(self, address: str, port: int) -> None:
        """Add an address to the address book (if not self and not duplicate).

        The address book is maintained in alphabetical order by 'address:port'.

        Args:
            address: IP address to add.
            port: Port number to add.
        """
        # Don't add self
        if address == self.address and port == self.port:
            return

        entry = f"{address}:{port}"
        # Don't add duplicates
        if entry in self.address_book:
            return

        self.address_book.append(entry)
        # Keep sorted alphabetically
        self.address_book.sort()

    def remove_from_address_book(self, address: str, port: int) -> None:
        """Remove an address from the address book.

        Args:
            address: IP address to remove.
            port: Port number to remove.
        """
        entry = f"{address}:{port}"
        if entry in self.address_book:
            self.address_book.remove(entry)

    def log_payload(self, payload: str) -> None:
        """Log a message payload for deduplication.

        Args:
            payload: The message payload to log.
        """
        # Don't add duplicates
        if payload not in self.message_log:
            self.message_log.append(payload)

    def clear_message_log(self) -> None:
        """Clear the message log."""
        self.message_log.clear()

    @property
    def is_single_node(self) -> bool:
        """Check if this is the only node in the ring.

        Returns:
            True if next_address and next_port are both None.
        """
        return self.next_address is None and self.next_port is None

    @property
    def self_address_str(self) -> str:
        """Get the node's address as a string.

        Returns:
            String in format 'address:port'.
        """
        return f"{self.address}:{self.port}"

    @property
    def next_address_str(self) -> str | None:
        """Get the next node's address as a string.

        Returns:
            String in format 'address:port' or None if no next node.
        """
        if self.next_address is None or self.next_port is None:
            return None
        return f"{self.next_address}:{self.next_port}"
