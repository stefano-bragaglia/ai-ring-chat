"""Tests for message parsing and formatting."""

import pytest

from ai_ring_chat.model.messages import (
    Address,
    Message,
    MessageType,
    format_echo,
    format_exit,
    format_join,
    format_next,
    format_ping,
    format_text,
    format_user,
    parse_message,
)


class TestAddress:
    """Tests for the Address class."""

    def test_parse_valid_address(self):
        """Test parsing valid address strings."""
        addr = Address.parse("127.0.0.1:5000")
        assert addr.address == "127.0.0.1"
        assert addr.port == 5000

    def test_parse_with_different_ip(self):
        """Test parsing different IP addresses."""
        addr = Address.parse("192.168.1.100:8080")
        assert addr.address == "192.168.1.100"
        assert addr.port == 8080

    def test_parse_invalid_no_colon(self):
        """Test that address without colon raises ValueError."""
        with pytest.raises(ValueError, match="Invalid address format"):
            Address.parse("127.0.0.1")

    def test_parse_invalid_port_not_number(self):
        """Test that non-numeric port raises ValueError."""
        with pytest.raises(ValueError, match="Invalid port"):
            Address.parse("127.0.0.1:abc")

    def test_parse_invalid_port_too_high(self):
        """Test that port > 65535 raises ValueError."""
        with pytest.raises(ValueError, match="Invalid port"):
            Address.parse("127.0.0.1:70000")

    def test_parse_invalid_port_negative(self):
        """Test that negative port raises ValueError."""
        with pytest.raises(ValueError, match="Invalid port"):
            Address.parse("127.0.0.1:-1")

    def test_parse_invalid_multiple_colons(self):
        """Test that address with multiple colons raises ValueError."""
        with pytest.raises(ValueError, match="Invalid port"):
            Address.parse("127.0.0.1:5000:extra")

    def test_str_representation(self):
        """Test string representation of Address."""
        addr = Address("127.0.0.1", 5000)
        assert str(addr) == "127.0.0.1:5000"


class TestParseMessage:
    """Tests for parse_message function."""

    def test_parse_join_message(self):
        """Test parsing a JOIN message."""
        msg = parse_message("JOIN 127.0.0.1:5000")
        assert msg is not None
        assert msg.msg_type == MessageType.JOIN
        assert msg.sender == Address("127.0.0.1", 5000)
        assert msg.content == ""

    def test_parse_join_lowercase(self):
        """Test parsing JOIN in lowercase."""
        msg = parse_message("join 127.0.0.1:5000")
        assert msg is not None
        assert msg.msg_type == MessageType.JOIN

    def test_parse_exit_message(self):
        """Test parsing an EXIT message."""
        msg = parse_message("EXIT 127.0.0.1:5000 127.0.0.1:5001")
        assert msg is not None
        assert msg.msg_type == MessageType.EXIT
        assert msg.sender == Address("127.0.0.1", 5000)
        assert msg.content == "127.0.0.1:5001"

    def test_parse_ping_message(self):
        """Test parsing a PING message."""
        msg = parse_message("PING 127.0.0.1:5000")
        assert msg is not None
        assert msg.msg_type == MessageType.PING
        assert msg.sender == Address("127.0.0.1", 5000)

    def test_parse_echo_message(self):
        """Test parsing an ECHO message."""
        msg = parse_message("ECHO 127.0.0.1:5000")
        assert msg is not None
        assert msg.msg_type == MessageType.ECHO
        assert msg.sender == Address("127.0.0.1", 5000)

    def test_parse_next_message(self):
        """Test parsing a NEXT message."""
        msg = parse_message("NEXT 127.0.0.1:5000")
        assert msg is not None
        assert msg.msg_type == MessageType.NEXT
        assert msg.sender == Address("127.0.0.1", 5000)

    def test_parse_text_message(self):
        """Test parsing a TEXT message."""
        msg = parse_message("TEXT Hello everyone!")
        assert msg is not None
        assert msg.msg_type == MessageType.TEXT
        assert msg.content == "Hello everyone!"

    def test_parse_text_message_with_multiple_words(self):
        """Test parsing TEXT with multiple words."""
        msg = parse_message("TEXT Hello world from the ring!")
        assert msg is not None
        assert msg.msg_type == MessageType.TEXT
        assert msg.content == "Hello world from the ring!"

    def test_parse_user_message(self):
        """Test parsing a USER message."""
        msg = parse_message("USER 127.0.0.1:5001 Hello private!")
        assert msg is not None
        assert msg.msg_type == MessageType.USER
        assert msg.content == "127.0.0.1:5001 Hello private!"

    def test_parse_invalid_empty_string(self):
        """Test that empty string returns None."""
        assert parse_message("") is None

    def test_parse_invalid_unknown_type(self):
        """Test that unknown message type returns None."""
        assert parse_message("UNKNOWN 127.0.0.1:5000") is None

    def test_parse_invalid_join_missing_address(self):
        """Test that JOIN without address returns None."""
        assert parse_message("JOIN") is None

    def test_parse_invalid_exit_missing_next(self):
        """Test that EXIT without next returns None."""
        assert parse_message("EXIT 127.0.0.1:5000") is None

    def test_parse_invalid_ping_missing_address(self):
        """Test that PING without address returns None."""
        assert parse_message("PING") is None

    def test_parse_invalid_echo_missing_address(self):
        """Test that ECHO without address returns None."""
        assert parse_message("ECHO") is None

    def test_parse_invalid_next_missing_address(self):
        """Test that NEXT without address returns None."""
        assert parse_message("NEXT") is None

    def test_parse_invalid_join_extra_tokens(self):
        """Test that JOIN with extra tokens returns None."""
        assert parse_message("JOIN 127.0.0.1:5000 extra") is None

    def test_parse_invalid_ping_extra_tokens(self):
        """Test that PING with extra tokens returns None."""
        assert parse_message("PING 127.0.0.1:5000 extra") is None

    def test_parse_invalid_echo_extra_tokens(self):
        """Test that ECHO with extra tokens returns None."""
        assert parse_message("ECHO 127.0.0.1:5000 extra") is None

    def test_parse_invalid_next_extra_tokens(self):
        """Test that NEXT with extra tokens returns None."""
        assert parse_message("NEXT 127.0.0.1:5000 extra") is None

    def test_parse_invalid_text_empty_payload(self):
        """Test that TEXT with empty payload returns None."""
        assert parse_message("TEXT") is None

    def test_parse_invalid_address_in_message(self):
        """Test that invalid address in message returns None (triggers except block)."""
        # This should trigger the ValueError exception handler
        assert parse_message("JOIN 127.0.0.1") is None

    def test_parse_invalid_address_port_not_number(self):
        """Test that non-numeric port in message returns None."""
        assert parse_message("PING 127.0.0.1:abc") is None

    def test_parse_invalid_exit_missing_args(self):
        """Test that EXIT with missing args returns None."""
        assert parse_message("EXIT 127.0.0.1:5000") is None

    def test_parse_invalid_user_missing_target(self):
        """Test that USER without target returns None."""
        assert parse_message("USER Hello") is None


class TestFormatFunctions:
    """Tests for message formatting functions."""

    def test_format_join(self):
        """Test formatting JOIN message."""
        sender = Address("127.0.0.1", 5000)
        result = format_join(sender)
        assert result == "JOIN 127.0.0.1:5000"

    def test_format_exit(self):
        """Test formatting EXIT message."""
        sender = Address("127.0.0.1", 5000)
        next_addr = Address("127.0.0.1", 5001)
        result = format_exit(sender, next_addr)
        assert result == "EXIT 127.0.0.1:5000 127.0.0.1:5001"

    def test_format_ping(self):
        """Test formatting PING message."""
        sender = Address("127.0.0.1", 5000)
        result = format_ping(sender)
        assert result == "PING 127.0.0.1:5000"

    def test_format_echo(self):
        """Test formatting ECHO message."""
        sender = Address("127.0.0.1", 5000)
        result = format_echo(sender)
        assert result == "ECHO 127.0.0.1:5000"

    def test_format_next(self):
        """Test formatting NEXT message."""
        sender = Address("127.0.0.1", 5000)
        result = format_next(sender)
        assert result == "NEXT 127.0.0.1:5000"

    def test_format_text(self):
        """Test formatting TEXT message."""
        result = format_text("Hello everyone!")
        assert result == "TEXT Hello everyone!"

    def test_format_user(self):
        """Test formatting USER message."""
        target = Address("127.0.0.1", 5001)
        result = format_user(target, "Hello private!")
        assert result == "USER 127.0.0.1:5001 Hello private!"


class TestMessageStr:
    """Tests for Message.__str__ method."""

    def test_message_str_control(self):
        """Test __str__ for control messages (with sender)."""
        msg = Message(
            msg_type=MessageType.PING,
            sender=Address("127.0.0.1", 5000),
            content="",
        )
        assert str(msg) == "PING 127.0.0.1:5000 "

    def test_message_str_text(self):
        """Test __str__ for TEXT message."""
        msg = Message(
            msg_type=MessageType.TEXT,
            sender=Address("0.0.0.0", 0),
            content="Hello!",
        )
        assert str(msg) == "TEXT Hello!"

    def test_message_str_user(self):
        """Test __str__ for USER message."""
        msg = Message(
            msg_type=MessageType.USER,
            sender=Address("0.0.0.0", 0),
            content="127.0.0.1:5001 Hello!",
        )
        assert str(msg) == "USER 127.0.0.1:5001 Hello!"
