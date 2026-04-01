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

        addr, port_str = value.rsplit(":", 1)

        try:
            port = int(port_str)
        except ValueError:
            raise ValueError(
                f"Invalid port in address: '{value}' (port must be integer)"
            )

        if 0 <= port <= 65535:
            return cls(address=addr, port=port)

        raise ValueError(f"Invalid port in address: '{value}' (port must be 0-65535)")


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

    # Parse based on message type using helper functions
    parsers = {
        MessageType.JOIN: _parse_join,
        MessageType.EXIT: _parse_exit,
        MessageType.PING: _parse_ping,
        MessageType.ECHO: _parse_echo,
        MessageType.NEXT: _parse_next,
        MessageType.TEXT: _parse_text,
        MessageType.USER: _parse_user,
    }

    try:
        return parsers[msg_type](parts)
    except ValueError, IndexError:
        return None


def _parse_join(parts: list[str]) -> Message | None:
    """Parse JOIN message."""
    if len(parts) != 2:
        return None
    return Message(
        msg_type=MessageType.JOIN, sender=Address.parse(parts[1]), content=""
    )


def _parse_exit(parts: list[str]) -> Message | None:
    """Parse EXIT message."""
    if len(parts) != 3:
        return None
    sender = Address.parse(parts[1])
    next_addr = Address.parse(parts[2])
    return Message(msg_type=MessageType.EXIT, sender=sender, content=str(next_addr))


def _parse_ping(parts: list[str]) -> Message | None:
    """Parse PING message."""
    if len(parts) != 2:
        return None
    return Message(
        msg_type=MessageType.PING, sender=Address.parse(parts[1]), content=""
    )


def _parse_echo(parts: list[str]) -> Message | None:
    """Parse ECHO message."""
    if len(parts) != 2:
        return None
    return Message(
        msg_type=MessageType.ECHO, sender=Address.parse(parts[1]), content=""
    )


def _parse_next(parts: list[str]) -> Message | None:
    """Parse NEXT message."""
    if len(parts) != 2:
        return None
    return Message(
        msg_type=MessageType.NEXT, sender=Address.parse(parts[1]), content=""
    )


def _parse_text(parts: list[str]) -> Message | None:
    """Parse TEXT message."""
    if len(parts) < 2:
        return None
    return Message(
        msg_type=MessageType.TEXT,
        sender=Address("0.0.0.0", 0),
        content=" ".join(parts[1:]),
    )


def _parse_user(parts: list[str]) -> Message | None:
    """Parse USER message."""
    if len(parts) < 3:
        return None
    target = Address.parse(parts[1])
    payload = " ".join(parts[2:])
    return Message(
        msg_type=MessageType.USER,
        sender=Address("0.0.0.0", 0),
        content=f"{target} {payload}",
    )


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
