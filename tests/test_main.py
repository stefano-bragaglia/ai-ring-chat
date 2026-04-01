"""Tests for argument parsing in main.py."""

import argparse

import pytest

from ai_ring_chat.main import (
    PRIVILEGED_PORT_THRESHOLD,
    DEFAULT_PROTOCOL_PORT,
    parse_join_target,
    validate_port,
    parse_args,
    NodeConfig,
)


class TestValidatePort:
    """Tests for validate_port function."""

    def test_valid_port(self):
        """Valid ports should not raise."""
        validate_port(57782)
        validate_port(1024)
        validate_port(65535)
        validate_port(0)

    def test_invalid_port_negative(self):
        """Negative ports should raise."""
        with pytest.raises(argparse.ArgumentTypeError) as exc_info:
            validate_port(-1)
        assert "-1" in str(exc_info.value)

    def test_invalid_port_too_high(self):
        """Ports > 65535 should raise."""
        with pytest.raises(argparse.ArgumentTypeError) as exc_info:
            validate_port(65536)
        assert "65535" in str(exc_info.value)

    def test_test_mode_port_below_threshold(self):
        """Test mode ports <= 1024 should raise."""
        with pytest.raises(argparse.ArgumentTypeError) as exc_info:
            validate_port(1024, is_test_mode=True)
        assert "1024" in str(exc_info.value)

    def test_test_mode_port_above_threshold(self):
        """Test mode ports > 1024 should not raise."""
        validate_port(1025, is_test_mode=True)
        validate_port(9000, is_test_mode=True)


class TestParseJoinTarget:
    """Tests for parse_join_target function."""

    def test_full_address_port_normal_mode(self):
        """Full address:port format in normal mode."""
        addr, port = parse_join_target("192.168.1.100:57782", test_mode=False)
        assert addr == "192.168.1.100"
        assert port == 57782

    def test_full_address_port_test_mode(self):
        """Full address:port format in test mode."""
        addr, port = parse_join_target("127.0.0.1:9000", test_mode=True)
        assert addr == "127.0.0.1"
        assert port == 9000

    def test_address_only_normal_mode(self):
        """Address only in normal mode (uses default port)."""
        addr, port = parse_join_target("192.168.1.100", test_mode=False)
        assert addr == "192.168.1.100"
        assert port == 57782

    def test_port_only_test_mode(self):
        """Port only in test mode (uses localhost)."""
        addr, port = parse_join_target("9000", test_mode=True)
        assert addr == "127.0.0.1"
        assert port == 9000

    def test_invalid_format(self):
        """Invalid format (multiple colons) should raise."""
        with pytest.raises(argparse.ArgumentTypeError) as exc_info:
            parse_join_target("invalid:format:too:many", test_mode=False)
        assert "Invalid" in str(exc_info.value)

    def test_invalid_port_non_numeric(self):
        """Non-numeric port should raise."""
        with pytest.raises(argparse.ArgumentTypeError) as exc_info:
            parse_join_target("192.168.1.100:abc", test_mode=False)
        assert "not a number" in str(exc_info.value)

    def test_ipv6_address_with_port(self):
        """IPv6 addresses should work."""
        addr, port = parse_join_target("[::1]:9000", test_mode=False)
        assert addr == "[::1]"
        assert port == 9000

    def test_hostname_with_port(self):
        """Hostnames with port should work."""
        addr, port = parse_join_target("localhost:57782", test_mode=False)
        assert addr == "localhost"
        assert port == 57782


class TestParseArgs:
    """Tests for parse_args function."""

    def test_local_mode_only(self):
        """Test mode with just --local."""
        config = parse_args(["--local", "9000"])
        assert config.is_test_mode is True
        assert config.address == "127.0.0.1"
        assert config.port == 9000
        assert config.join_address is None
        assert config.join_port is None

    def test_local_mode_short_flag(self):
        """Test mode with -l short flag."""
        config = parse_args(["-l", "9000"])
        assert config.is_test_mode is True
        assert config.port == 9000

    def test_normal_mode_join_full_address(self):
        """Normal mode with full address:port join target."""
        config = parse_args(["--join", "192.168.1.100:57782"])
        assert config.is_test_mode is False
        assert config.port == DEFAULT_PROTOCOL_PORT
        assert config.join_address == "192.168.1.100"
        assert config.join_port == 57782

    def test_normal_mode_join_address_only(self):
        """Normal mode with address-only join target (uses default port)."""
        config = parse_args(["--join", "192.168.1.100"])
        assert config.is_test_mode is False
        assert config.join_address == "192.168.1.100"
        assert config.join_port == DEFAULT_PROTOCOL_PORT

    def test_test_mode_join_full_address(self):
        """Test mode with full address:port join target."""
        config = parse_args(["--local", "9000", "--join", "127.0.0.1:57782"])
        assert config.is_test_mode is True
        assert config.port == 9000
        assert config.join_address == "127.0.0.1"
        assert config.join_port == 57782

    def test_test_mode_join_port_only(self):
        """Test mode with port-only join target (uses localhost)."""
        config = parse_args(["--local", "9000", "--join", "57782"])
        assert config.is_test_mode is True
        assert config.port == 9000
        assert config.join_address == "127.0.0.1"
        assert config.join_port == 57782

    def test_local_port_too_low(self):
        """Local port <= 1024 should raise."""
        with pytest.raises(argparse.ArgumentTypeError) as exc_info:
            parse_args(["--local", "1024"])
        assert "1024" in str(exc_info.value)

    def test_local_port_1025(self):
        """Local port 1025 should work."""
        config = parse_args(["--local", "1025"])
        assert config.port == 1025

    def test_join_invalid_format(self):
        """Invalid join format should raise."""
        with pytest.raises(argparse.ArgumentTypeError) as exc_info:
            parse_args(["--join", "invalid:format:too:many"])
        assert "Invalid port" in str(exc_info.value)

    def test_mutually_exclusive(self):
        """--local and --join are mutually exclusive? Actually they aren't in our design."""

    def test_both_flags(self):
        """Both flags together should work (test mode with join target)."""
        config = parse_args(["--local", "9000", "--join", "9001"])
        assert config.is_test_mode is True
        assert config.port == 9000
        assert config.join_address == "127.0.0.1"
        assert config.join_port == 9001

    def test_no_arguments(self):
        """No arguments creates a new ring node (normal mode, no join)."""
        config = parse_args([])
        assert config.is_test_mode is False
        assert config.join_address is None
        assert config.join_port is None


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
            port=57782,
            is_test_mode=False,
            join_address=None,
            join_port=None,
        )
        assert config.join_address is None
        assert config.join_port is None
