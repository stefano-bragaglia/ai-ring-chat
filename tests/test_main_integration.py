"""Tests for the main module integration."""

from unittest.mock import MagicMock, patch
from io import StringIO

from ai_ring_chat.main import parse_args, main


class TestParseArgs:
    """Tests for argument parsing."""

    def test_parse_args_normal_mode_first_node(self):
        """Test parsing args for first node in normal mode."""
        config = parse_args([])
        assert config.address is not None
        assert config.port == 57782
        assert config.is_test_mode is False
        assert config.join_address is None

    def test_parse_args_normal_mode_join(self):
        """Test parsing args for joining a ring."""
        config = parse_args(["--join", "192.168.1.100"])
        assert config.join_address == "192.168.1.100"
        assert config.join_port == 57782

    def test_parse_args_test_mode_self(self):
        """Test parsing args for test mode."""
        config = parse_args(["--self", "9000"])
        assert config.address == "127.0.0.1"
        assert config.port == 9000
        assert config.is_test_mode is True

    def test_parse_args_test_mode_join(self):
        """Test parsing args for test mode with join."""
        config = parse_args(["--self", "9000", "--join", "9001"])
        assert config.address == "127.0.0.1"
        assert config.port == 9000
        assert config.join_address == "127.0.0.1"
        assert config.join_port == 9001


class TestMain:
    """Tests for main function."""

    @patch("ai_ring_chat.main.get_ipv4_address")
    @patch("ai_ring_chat.main.TkinterView")
    @patch("ai_ring_chat.main.TkinterController")
    def test_main_first_node(self, mock_controller, mock_view, mock_get_ip):
        """Test main() for first node (no join)."""
        mock_get_ip.return_value = "127.0.0.1"
        mock_view_instance = MagicMock()
        mock_view.return_value = mock_view_instance
        mock_controller_instance = MagicMock()
        mock_controller.return_value = mock_controller_instance

        with patch("sys.stdout", new=StringIO()) as mock_stdout:
            result = main([])

        assert result == 0
        output = mock_stdout.getvalue()
        assert "127.0.0.1" in output
        assert "57782" in output

    @patch("ai_ring_chat.main.get_ipv4_address")
    @patch("ai_ring_chat.main.TkinterView")
    @patch("ai_ring_chat.main.TkinterController")
    @patch("ai_ring_chat.main.network")
    def test_main_with_join(
        self, mock_network, mock_controller, mock_view, mock_get_ip
    ):
        """Test main() when joining existing ring."""
        mock_get_ip.return_value = "127.0.0.1"
        mock_network.send.return_value = True
        mock_network.parse_message.return_value = MagicMock()
        mock_view_instance = MagicMock()
        mock_view.return_value = mock_view_instance
        mock_controller_instance = MagicMock()
        mock_controller.return_value = mock_controller_instance

        with patch("sys.stdout", new=StringIO()) as mock_stdout:
            result = main(["--join", "192.168.1.100"])

        assert result == 0
        output = mock_stdout.getvalue()
        assert "Joining" in output
        assert "192.168.1.100" in output

    @patch("ai_ring_chat.main.get_ipv4_address")
    @patch("ai_ring_chat.main.TkinterView")
    @patch("ai_ring_chat.main.TkinterController")
    def test_main_test_mode(self, mock_controller, mock_view, mock_get_ip):
        """Test main() in test mode."""
        mock_view_instance = MagicMock()
        mock_view.return_value = mock_view_instance
        mock_controller_instance = MagicMock()
        mock_controller.return_value = mock_controller_instance

        with patch("sys.stdout", new=StringIO()) as mock_stdout:
            result = main(["--self", "9000"])

        assert result == 0
        output = mock_stdout.getvalue()
        assert "TEST" in output
        assert "9000" in output


class TestMainIntegration:
    """Integration tests for main with controller."""

    @patch("ai_ring_chat.main.get_ipv4_address")
    @patch("ai_ring_chat.main.TkinterController")
    @patch("ai_ring_chat.main.TkinterView")
    def test_main_integration_flow(self, mock_view, mock_controller, mock_get_ip):
        """Test the full integration flow."""
        mock_get_ip.return_value = "127.0.0.1"

        # Setup mocks
        mock_node = MagicMock()
        mock_node.address = "127.0.0.1"
        mock_node.port = 57782
        mock_node.self_address_str = "127.0.0.1:57782"

        mock_controller_instance = MagicMock()
        mock_controller.return_value = mock_controller_instance

        mock_view_instance = MagicMock()
        mock_view.return_value = mock_view_instance

        with patch("ai_ring_chat.main.Node", return_value=mock_node):
            with patch("ai_ring_chat.main.network") as mock_network:
                mock_network.send.return_value = True
                mock_network.parse_message.return_value = MagicMock()
                _ = main([])

        # Should create Node, View, and Controller
        mock_view.assert_called_once()
        mock_controller.assert_called_once()

        # Controller should be started
        mock_controller_instance.start.assert_called_once()

    @patch("ai_ring_chat.main.get_ipv4_address")
    @patch("ai_ring_chat.main.TkinterController")
    @patch("ai_ring_chat.main.TkinterView")
    def test_main_integration_with_join(self, mock_view, mock_controller, mock_get_ip):
        """Test integration when joining an existing ring."""
        mock_get_ip.return_value = "127.0.0.1"

        # Setup mocks
        mock_node = MagicMock()
        mock_node.address = "127.0.0.1"
        mock_node.port = 57782
        mock_node.self_address_str = "127.0.0.1:57782"
        mock_node.next_address = None
        mock_node.next_port = None

        mock_controller_instance = MagicMock()
        mock_controller.return_value = mock_controller_instance

        mock_view_instance = MagicMock()
        mock_view.return_value = mock_view_instance

        with patch("ai_ring_chat.main.Node", return_value=mock_node):
            with patch("ai_ring_chat.main.network") as mock_network:
                mock_network.send.return_value = True
                mock_network.parse_message.return_value = MagicMock()
                _ = main(["--join", "192.168.1.100"])

        # Should have sent a JOIN message
        assert mock_network.send.call_count >= 1
