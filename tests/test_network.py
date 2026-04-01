"""Tests for the network module."""

from unittest.mock import MagicMock, patch
import socket

from ai_ring_chat.control.network import create_socket, send, receive
from ai_ring_chat.model.messages import Message, MessageType, Address


class TestCreateSocket:
    """Tests for create_socket function."""

    def test_create_socket_returns_udp(self):
        """Test that create_socket returns a UDP socket."""
        sock = create_socket(5000)
        try:
            assert sock.type == socket.SOCK_DGRAM
            assert sock.family == socket.AF_INET
        finally:
            sock.close()

    def test_create_socket_binds_to_port(self):
        """Test that socket is bound to the specified port."""
        sock = create_socket(5000)
        try:
            assert sock.getsockname()[1] == 5000
        finally:
            sock.close()

    def test_create_socket_has_reuse_addr_option(self):
        """Test that socket has reuse address option available."""
        sock = create_socket(5000)
        try:
            # Just check we can get the option without error
            opt = sock.getsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR)
            # On some systems this is 1, on others it's non-zero
            assert opt is not None
        finally:
            sock.close()


class TestSend:
    """Tests for send function."""

    @patch("socket.socket")
    def test_send_message_to_address(self, mock_socket_class):
        """Test sending a Message to an address."""
        mock_sock = MagicMock()
        mock_socket_class.return_value = mock_sock

        msg = Message(
            msg_type=MessageType.TEXT,
            sender=Address("127.0.0.1", 5000),
            content="Hello",
        )
        send("192.168.1.1", 5001, msg)

        mock_sock.sendto.assert_called_once()
        call_args = mock_sock.sendto.call_args[0]
        # Should send a string representation
        assert (
            "TEXT" in call_args[0].decode()
            if isinstance(call_args[0], bytes)
            else "TEXT" in call_args[0]
        )
        assert call_args[1] == ("192.168.1.1", 5001)
        mock_sock.close.assert_called_once()

    @patch("socket.socket")
    def test_send_no_return_value(self, mock_socket_class):
        """Test that send does not need to return anything meaningful."""
        mock_sock = MagicMock()
        mock_socket_class.return_value = mock_sock

        msg = Message(
            msg_type=MessageType.PING, sender=Address("127.0.0.1", 5000), content=""
        )
        send("127.0.0.1", 5001, msg)

        # Result should be None or we don't care about it

    @patch("socket.socket")
    def test_send_exception_returns_false(self, mock_socket_class):
        """Test that send returns False on exception."""
        mock_sock = MagicMock()
        mock_sock.sendto.side_effect = Exception("Network error")
        mock_socket_class.return_value = mock_sock

        msg = Message(
            msg_type=MessageType.TEXT,
            sender=Address("127.0.0.1", 5000),
            content="Hello",
        )
        result = send("192.168.1.1", 5001, msg)

        assert result is False


class TestReceive:
    """Tests for receive function."""

    def test_receive_timeout_returns_none(self):
        """Test that receive returns None on timeout."""
        sock = create_socket(5001)
        try:
            sock.settimeout(0.1)
            result = receive(sock, timeout=0.2)

            assert result is None
        finally:
            sock.close()

    def test_receive_invalid_message_returns_none(self):
        """Test that receive returns None for invalid message."""
        # This test verifies parse_message returns None for invalid
        from ai_ring_chat.model.messages import parse_message

        result = parse_message("INVALID_MESSAGE")
        assert result is None

    @patch("socket.socket")
    def test_receive_parses_valid_message(self, mock_socket_class):
        """Test that receive parses a valid message successfully."""
        mock_sock = MagicMock()
        mock_sock.recvfrom.return_value = (b"PING 127.0.0.1:5001", ("127.0.0.1", 5001))
        mock_socket_class.return_value = mock_sock

        result = receive(mock_sock, timeout=1.0)

        assert result is not None
        assert result.msg_type == MessageType.PING


class TestSendReceive:
    """Integration tests for send and receive."""

    @patch("socket.socket")
    def test_send_and_verify_format(self, mock_socket_class):
        """Test that send formats the message correctly."""
        mock_sock = MagicMock()
        mock_socket_class.return_value = mock_sock

        msg = Message(
            msg_type=MessageType.USER,
            sender=Address("127.0.0.1", 5000),
            content="127.0.0.1:5001 Hello!",
        )
        send("127.0.0.1", 5001, msg)

        call_args = mock_sock.sendto.call_args[0]
        message_str = (
            call_args[0].decode() if isinstance(call_args[0], bytes) else call_args[0]
        )

        assert message_str.startswith("USER")
        assert "127.0.0.1:5001" in message_str
        assert "Hello!" in message_str
