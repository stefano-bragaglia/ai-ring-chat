"""Tests for argument parsing in main.py."""

import argparse
from unittest.mock import MagicMock, patch

import pytest

from ai_ring_chat.main import (
    DEFAULT_PROTOCOL_PORT,
    parse_port,
    is_valid_ipv4,
    parse_join_target,
    parse_args,
    get_ipv4_address,
    main,
    NodeConfig,
)


class TestIsValidIPv4:
    """Tests for is_valid_ipv4 function."""

    def test_valid_addresses(self):
        """Valid IPv4 addresses should return True."""
        assert is_valid_ipv4("192.168.1.1") is True
        assert is_valid_ipv4("127.0.0.1") is True
        assert is_valid_ipv4("0.0.0.0") is True
        assert is_valid_ipv4("255.255.255.255") is True
        assert is_valid_ipv4("10.0.0.1") is True
        assert is_valid_ipv4("172.16.0.1") is True

    def test_invalid_addresses(self):
        """Invalid addresses should return False."""
        assert is_valid_ipv4("192.168.1") is False
        assert is_valid_ipv4("192.168.1.1.1") is False
        assert is_valid_ipv4("256.0.0.1") is False
        assert is_valid_ipv4("192.168.1.300") is False
        assert is_valid_ipv4("192.168.1.-1") is False
        assert is_valid_ipv4("abc.def.ghi.jkl") is False
        assert is_valid_ipv4("192.168.1.1:57782") is False
        assert is_valid_ipv4("") is False
        assert is_valid_ipv4("localhost") is False


class TestParsePort:
    """Tests for parse_port function."""

    def test_valid_port(self):
        """Valid ports should return the port number."""
        assert parse_port("1025", "--self") == 1025
        assert parse_port("9000", "--join") == 9000
        assert parse_port("57782", "--self") == 57782
        assert parse_port("65535", "--join") == 65535

    def test_non_numeric(self):
        """Non-numeric port should raise."""
        with pytest.raises(argparse.ArgumentTypeError) as exc_info:
            parse_port("abc", "--join")
        assert "not a number" in str(exc_info.value)

    def test_port_too_low_negative(self):
        """Port < 0 should raise."""
        with pytest.raises(argparse.ArgumentTypeError) as exc_info:
            parse_port("-1", "--join")
        assert "root privileges" in str(exc_info.value)

    def test_port_too_high(self):
        """Port > 65535 should raise."""
        with pytest.raises(argparse.ArgumentTypeError) as exc_info:
            parse_port("65536", "--join")
        assert "root privileges" in str(exc_info.value)

    def test_privileged_port(self):
        """Port <= 1024 should raise."""
        with pytest.raises(argparse.ArgumentTypeError) as exc_info:
            parse_port("1024", "--self")
        assert "root privileges" in str(exc_info.value)


class TestParseJoinTarget:
    """Tests for parse_join_target function."""

    def test_normal_mode_ipv4_address(self):
        """Normal mode: IPv4 address with default port."""
        addr, port = parse_join_target("192.168.1.100", is_test_mode=False)
        assert addr == "192.168.1.100"
        assert port == DEFAULT_PROTOCOL_PORT

    def test_normal_mode_invalid_address(self):
        """Normal mode: invalid address should raise."""
        with pytest.raises(argparse.ArgumentTypeError) as exc_info:
            parse_join_target("192.168.1.1:57782", is_test_mode=False)
        assert "Invalid IPv4 address" in str(exc_info.value)

    def test_normal_mode_with_port_rejected(self):
        """Normal mode: address:port format should raise."""
        with pytest.raises(argparse.ArgumentTypeError) as exc_info:
            parse_join_target("192.168.1.100:57782", is_test_mode=False)
        assert "Invalid IPv4 address" in str(exc_info.value)

    def test_normal_mode_hostname_rejected(self):
        """Normal mode: hostname should raise."""
        with pytest.raises(argparse.ArgumentTypeError) as exc_info:
            parse_join_target("localhost", is_test_mode=False)
        assert "Invalid IPv4 address" in str(exc_info.value)

    def test_test_mode_port(self):
        """Test mode: port number with localhost."""
        addr, port = parse_join_target("9001", is_test_mode=True)
        assert addr == "127.0.0.1"
        assert port == 9001

    def test_test_mode_ipv4_rejected(self):
        """Test mode: IPv4 address should raise (expect port only)."""
        with pytest.raises(argparse.ArgumentTypeError) as exc_info:
            parse_join_target("192.168.1.100", is_test_mode=True)
        assert "not a number" in str(exc_info.value)


class TestParseArgs:
    """Tests for parse_args function."""

    def test_no_arguments_normal_mode(self):
        """No arguments creates normal mode node."""
        config = parse_args([])
        assert config.is_test_mode is False
        assert config.port == DEFAULT_PROTOCOL_PORT
        assert config.join_address is None
        assert config.join_port is None

    def test_self_mode_only(self):
        """Test mode with just --self."""
        config = parse_args(["--self", "9000"])
        assert config.is_test_mode is True
        assert config.address == "127.0.0.1"
        assert config.port == 9000
        assert config.join_address is None
        assert config.join_port is None

    def test_self_mode_short_flag(self):
        """Test mode with -s short flag."""
        config = parse_args(["-s", "9000"])
        assert config.is_test_mode is True
        assert config.port == 9000

    def test_normal_mode_join_ipv4(self):
        """Normal mode with IPv4 address join target."""
        config = parse_args(["--join", "192.168.1.100"])
        assert config.is_test_mode is False
        assert config.port == DEFAULT_PROTOCOL_PORT
        assert config.join_address == "192.168.1.100"
        assert config.join_port == DEFAULT_PROTOCOL_PORT

    def test_normal_mode_join_ipv4_short_flag(self):
        """Normal mode with -j short flag."""
        config = parse_args(["-j", "10.0.0.1"])
        assert config.join_address == "10.0.0.1"

    def test_test_mode_join_port(self):
        """Test mode with port-only join target."""
        config = parse_args(["--self", "9000", "--join", "9001"])
        assert config.is_test_mode is True
        assert config.port == 9000
        assert config.join_address == "127.0.0.1"
        assert config.join_port == 9001

    def test_self_port_too_low(self):
        """--self port <= 1024 should raise."""
        with pytest.raises(argparse.ArgumentTypeError) as exc_info:
            parse_args(["--self", "1024"])
        assert "greater than 1024" in str(exc_info.value)

    def test_self_port_1025(self):
        """--self port 1025 should work."""
        config = parse_args(["--self", "1025"])
        assert config.port == 1025

    def test_join_invalid_ipv4_normal_mode(self):
        """Invalid IPv4 in normal mode should raise."""
        with pytest.raises(argparse.ArgumentTypeError) as exc_info:
            parse_args(["--join", "invalid"])
        assert "Invalid IPv4 address" in str(exc_info.value)

    def test_join_port_as_address_rejected(self):
        """Port-only in normal mode should raise."""
        with pytest.raises(argparse.ArgumentTypeError) as exc_info:
            parse_args(["--join", "9000"])
        assert "Invalid IPv4 address" in str(exc_info.value)


class TestNodeConfig:
    """Tests for NodeConfig dataclass."""

    def test_creation(self):
        """NodeConfig can be created."""
        config = NodeConfig(
            address="127.0.0.1",
            port=9000,
            is_test_mode=True,
            join_address="127.0.0.1",
            join_port=57782,
        )
        assert config.address == "127.0.0.1"
        assert config.port == 9000
        assert config.is_test_mode is True
        assert config.join_address == "127.0.0.1"
        assert config.join_port == 57782

    def test_optional_join(self):
        """Join fields can be None for first node."""
        config = NodeConfig(
            address="192.168.1.100",
            port=DEFAULT_PROTOCOL_PORT,
            is_test_mode=False,
            join_address=None,
            join_port=None,
        )
        assert config.join_address is None
        assert config.join_port is None


class TestGetIPv4Address:
    """Tests for get_ipv4_address function."""

    def test_returns_detected_ip(self):
        """Should return IP from socket connection."""
        with patch("socket.socket") as mock_socket:
            mock_instance = mock_socket.return_value
            mock_instance.getsockname.return_value = ("192.168.1.100",)
            result = get_ipv4_address()
            assert result == "192.168.1.100"
            mock_instance.connect.assert_called_once()
            mock_instance.close.assert_called_once()

    def test_fallback_on_exception(self):
        """Should return 127.0.0.1 when socket fails."""
        with patch("socket.socket") as mock_socket:
            mock_socket.side_effect = OSError("Network unavailable")
            result = get_ipv4_address()
            assert result == "127.0.0.1"


class TestMain:
    """Tests for main function."""

    @patch("ai_ring_chat.main.TkinterView")
    @patch("ai_ring_chat.main.TkinterController")
    def test_main_normal_mode(self, mock_controller, mock_view, capsys):
        """Main should print configuration for normal mode."""
        mock_view_instance = MagicMock()
        mock_view.return_value = mock_view_instance
        mock_controller_instance = MagicMock()
        mock_controller.return_value = mock_controller_instance
        mock_controller_instance.start.return_value = None

        with patch("sys.argv", ["ai-ring-chat"]):
            with patch("ai_ring_chat.main.network"):
                result = main()

        assert result == 0
        captured = capsys.readouterr()
        assert "AI-Ring-Chat Node Configuration" in captured.out
        assert "NORMAL" in captured.out
        assert "57782" in captured.out

    @patch("ai_ring_chat.main.TkinterView")
    @patch("ai_ring_chat.main.TkinterController")
    def test_main_test_mode(self, mock_controller, mock_view, capsys):
        """Main should print configuration for test mode."""
        mock_view_instance = MagicMock()
        mock_view.return_value = mock_view_instance
        mock_controller_instance = MagicMock()
        mock_controller.return_value = mock_controller_instance
        mock_controller_instance.start.return_value = None

        with patch("sys.argv", ["ai-ring-chat", "--self", "9000"]):
            with patch("ai_ring_chat.main.network"):
                result = main()

        assert result == 0
        captured = capsys.readouterr()
        assert "TEST" in captured.out
        assert "9000" in captured.out
        assert "127.0.0.1" in captured.out

    @patch("ai_ring_chat.main.TkinterView")
    @patch("ai_ring_chat.main.TkinterController")
    def test_main_with_join(self, mock_controller, mock_view, capsys):
        """Main should show join target when specified."""
        mock_view_instance = MagicMock()
        mock_view.return_value = mock_view_instance
        mock_controller_instance = MagicMock()
        mock_controller.return_value = mock_controller_instance
        mock_controller_instance.start.return_value = None

        with patch("sys.argv", ["ai-ring-chat", "--join", "192.168.1.100"]):
            with patch("ai_ring_chat.main.network") as mock_network:
                mock_network.parse_message.return_value = MagicMock()
                mock_network.send.return_value = True
                result = main()

        assert result == 0
        captured = capsys.readouterr()
        assert "Joining:" in captured.out
        assert "192.168.1.100" in captured.out
