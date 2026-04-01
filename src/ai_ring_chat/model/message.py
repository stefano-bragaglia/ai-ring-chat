"""Message types and parsing for the ring chat protocol."""

from dataclasses import dataclass
from enum import Enum
from typing import NamedTuple


class MessageType(Enum):
    """All supported message types in the protocol."""

    JOIN = "JOIN"
    EXIT = "EXIT"
    PING = "PING"
    ECHO = "ECHO"
    NEXT = "NEXT"
    TEXT = "TEXT"
    USER = "USER"


class Address(NamedTuple):
    """Represents a node's network address."""

    address: str
    port: int

    def __str__(self) -> str:
        return f"{self.address}:{self.port}"

    @classmethod
    def parse(cls, value: str) -> "Address":
        """Parse an address string like '127.0.0.1:5000'.

        Args:
            value: String in format 'address:port'

        Returns:
            Address instance

        Raises:
            ValueError: If format is invalid
        """
        if ":" not in value:
            raise ValueError(
                f"Invalid address format: '{value}' (expected 'address:port')"
            )

        parts = value.rsplit(":", 1)
        if len(parts) != 2:
            raise ValueError(f"Invalid address format: '{value}'")

        addr, port_str = parts
        try:
            port = int(port_str)
        except ValueError:
            raise ValueError(
                f"Invalid port in address: '{value}' (port must be integer)"
            )

        if port < 0 or port > 65535:
            raise ValueError(
                f"Invalid port in address: '{value}' (port must be 0-65535)"
            )

        return cls(address=addr, port=port)


@dataclass
class Message:
    """Represents a parsed message from the protocol."""

    msg_type: MessageType
    sender: Address
    content: str  # The remaining content after the message type

    def __str__(self) -> str:
        """Format the message for network transmission."""
        if self.msg_type in (MessageType.TEXT, MessageType.USER):
            return f"{self.msg_type.value} {self.content}"
        return f"{self.msg_type.value} {self.sender} {self.content}"


def parse_message(data: str) -> Message | None:
    """Parse a raw message string into a Message object.

    Args:
        data: Raw message string (e.g., 'JOIN 127.0.0.1:5000')

    Returns:
        Message instance if parsing succeeds, None if invalid

    Message formats:
        - JOIN <sender>
        - EXIT <sender> <next>
        - PING <sender>
        - ECHO <sender>
        - NEXT <sender>
        - TEXT <payload>
        - USER <target> <payload>
    """
    if not data:
        return None

    parts = data.split()
    if len(parts) < 2:
        return None

    msg_type_str = parts[0].upper()
    try:
        msg_type = MessageType(msg_type_str)
    except ValueError:
        return None

    # Parse based on message type
    try:
        match msg_type:
            case MessageType.JOIN:
                # JOIN <sender>
                if len(parts) != 2:
                    return None
                sender = Address.parse(parts[1])
                return Message(msg_type=msg_type, sender=sender, content="")

            case MessageType.EXIT:
                # EXIT <sender> <next>
                if len(parts) != 3:
                    return None
                sender = Address.parse(parts[1])
                next_addr = Address.parse(parts[2])
                return Message(msg_type=msg_type, sender=sender, content=str(next_addr))

            case MessageType.PING:
                # PING <sender>
                if len(parts) != 2:
                    return None
                sender = Address.parse(parts[1])
                return Message(msg_type=msg_type, sender=sender, content="")

            case MessageType.ECHO:
                # ECHO <sender>
                if len(parts) != 2:
                    return None
                sender = Address.parse(parts[1])
                return Message(msg_type=msg_type, sender=sender, content="")

            case MessageType.NEXT:
                # NEXT <sender>
                if len(parts) != 2:
                    return None
                sender = Address.parse(parts[1])
                return Message(msg_type=msg_type, sender=sender, content="")

            case MessageType.TEXT:
                # TEXT <payload>
                if len(parts) < 2:
                    return None
                payload = " ".join(parts[1:])
                # Sender is needed - we'll set it later or use empty
                return Message(
                    msg_type=msg_type, sender=Address("0.0.0.0", 0), content=payload
                )

            case MessageType.USER:
                # USER <target> <payload>
                if len(parts) < 3:
                    return None
                target = Address.parse(parts[1])
                payload = " ".join(parts[2:])
                return Message(
                    msg_type=msg_type,
                    sender=Address("0.0.0.0", 0),
                    content=f"{target} {payload}",
                )

    except ValueError, IndexError:
        return None


def format_join(sender: Address) -> str:
    """Format a JOIN message."""
    return f"JOIN {sender}"


def format_exit(sender: Address, next_addr: Address) -> str:
    """Format an EXIT message."""
    return f"EXIT {sender} {next_addr}"


def format_ping(sender: Address) -> str:
    """Format a PING message."""
    return f"PING {sender}"


def format_echo(sender: Address) -> str:
    """Format an ECHO response message."""
    return f"ECHO {sender}"


def format_next(sender: Address) -> str:
    """Format a NEXT (recovery) message."""
    return f"NEXT {sender}"


def format_text(payload: str) -> str:
    """Format a TEXT (public) message."""
    return f"TEXT {payload}"


def format_user(target: Address, payload: str) -> str:
    """Format a USER (private) message."""
    return f"USER {target} {payload}"
