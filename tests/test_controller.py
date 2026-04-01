"""Tests for the controller module."""

from unittest.mock import MagicMock, patch

from ai_ring_chat.control.controller import Controller, TkinterController
from ai_ring_chat.model.nodes import Node
from ai_ring_chat.model.messages import Message, MessageType, Address


class TestControllerInterface:
    """Tests to verify Controller is an abstract class."""

    def test_controller_is_abstract(self):
        """Test that Controller cannot be instantiated directly."""
        # Controller is abstract - trying to instantiate with ABC should fail
        # Check that Controller inherits from ABC
        from abc import ABC

        assert issubclass(Controller, ABC)


class TestTkinterController:
    """Tests for TkinterController implementation."""

    def test_controller_creation(self):
        """Test that TkinterController can be created."""
        node = Node(address="127.0.0.1", port=5000)
        view = MagicMock()
        controller = TkinterController(node, view)
        assert controller is not None

    def test_controller_stores_node(self):
        """Test that controller stores the node."""
        node = Node(address="127.0.0.1", port=5000)
        view = MagicMock()
        controller = TkinterController(node, view)
        assert controller._node is node

    def test_controller_stores_view(self):
        """Test that controller stores the view."""
        node = Node(address="127.0.0.1", port=5000)
        view = MagicMock()
        controller = TkinterController(node, view)
        assert controller._view is view

    def test_send_message(self):
        """Test sending a text message."""
        node = Node(
            address="127.0.0.1", port=5000, next_address="127.0.0.1", next_port=5001
        )
        view = MagicMock()
        view.get_message.return_value = "Hello world"
        controller = TkinterController(node, view)

        with patch("ai_ring_chat.control.network.send") as mock_send:
            mock_send.return_value = True
            controller.send_message()

        view.append_message.assert_called()

    def test_send_private_message(self):
        """Test sending a private message with @address:port prefix."""
        node = Node(
            address="127.0.0.1", port=5000, next_address="127.0.0.1", next_port=5001
        )
        view = MagicMock()
        view.get_message.return_value = "@127.0.0.1:5001 Hello private"
        controller = TkinterController(node, view)

        with patch("ai_ring_chat.control.network.send") as mock_send:
            mock_send.return_value = True
            controller.send_message()

    def test_send_empty_message(self):
        """Test that empty messages are not sent."""
        node = Node(
            address="127.0.0.1", port=5000, next_address="127.0.0.1", next_port=5001
        )
        view = MagicMock()
        view.get_message.return_value = ""
        controller = TkinterController(node, view)

        controller.send_message()

        # Should not call send or append message
        view.append_message.assert_not_called()

    def test_on_user_click(self):
        """Test that clicking a user prepends address to input."""
        node = Node(address="127.0.0.1", port=5000)
        view = MagicMock()
        controller = TkinterController(node, view)

        controller.on_user_click("127.0.0.1:5001")

        view.set_input_text.assert_called()

    def test_update_view_with_address_book(self):
        """Test that address book updates view user list."""
        node = Node(address="127.0.0.1", port=5000)
        node.add_to_address_book("127.0.0.1", 5001)
        node.add_to_address_book("127.0.0.1", 5002)

        view = MagicMock()
        controller = TkinterController(node, view)

        controller.update_user_list()

        view.update_user_list.assert_called()

    def test_handle_incoming_join(self):
        """Test handling incoming JOIN message."""
        node = Node(address="127.0.0.1", port=5000)
        view = MagicMock()
        controller = TkinterController(node, view)

        msg = Message(
            msg_type=MessageType.JOIN, sender=Address("127.0.0.1", 5001), content=""
        )

        with patch("ai_ring_chat.control.network.send") as mock_send:
            mock_send.return_value = True
            controller.handle_message(msg)

        # Should set next and update view
        assert node.next_address == "127.0.0.1"
        assert node.next_port == 5001
        view.update_user_list.assert_called()

    def test_handle_incoming_ping(self):
        """Test handling incoming PING message."""
        node = Node(address="127.0.0.1", port=5000)
        view = MagicMock()
        controller = TkinterController(node, view)

        msg = Message(
            msg_type=MessageType.PING, sender=Address("127.0.0.1", 5001), content=""
        )

        with patch("ai_ring_chat.control.network.send") as mock_send:
            mock_send.return_value = True
            controller.handle_message(msg)

        # Should record ping timestamp
        assert node.last_ping_received is not None

    def test_handle_incoming_text(self):
        """Test handling incoming TEXT message."""
        node = Node(address="127.0.0.1", port=5000)
        view = MagicMock()
        controller = TkinterController(node, view)

        msg = Message(
            msg_type=MessageType.TEXT,
            sender=Address("127.0.0.1", 5001),
            content="Hello from node 5001!",
        )

        with patch("ai_ring_chat.control.network.send") as mock_send:
            mock_send.return_value = True
            controller.handle_message(msg)

        # Should append message to view
        view.append_message.assert_called()

    def test_graceful_exit(self):
        """Test graceful exit sends EXIT message."""
        node = Node(
            address="127.0.0.1", port=5000, next_address="127.0.0.1", next_port=5001
        )
        view = MagicMock()
        controller = TkinterController(node, view)

        with patch("ai_ring_chat.control.network.send") as mock_send:
            mock_send.return_value = True
            controller.on_close()

        # Should have sent EXIT message
        mock_send.assert_called()


class TestControllerIntegration:
    """Integration tests for controller components."""

    def test_controller_with_view_callbacks(self):
        """Test controller properly sets up view callbacks."""
        node = Node(address="127.0.0.1", port=5000)
        view = MagicMock()
        TkinterController(node, view)

        # Verify callbacks are set
        view.set_send_callback.assert_called_once()
        view.set_user_click_callback.assert_called_once()
        view.set_close_callback.assert_called_once()

    def test_node_address_in_view_title(self):
        """Test that node address is used in view."""
        node = Node(address="192.168.1.100", port=5000)
        view = MagicMock()
        controller = TkinterController(node, view)

        # Verify the controller uses the node's address for internal operations
        assert controller._node.address == "192.168.1.100"
        assert controller._node.port == 5000
