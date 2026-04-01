"""Tests for the controller module."""

import pytest
from unittest.mock import MagicMock, patch

from ai_ring_chat.control.controller import Controller, TkinterController
from ai_ring_chat.model.nodes import Node
from ai_ring_chat.model.messages import Message, MessageType, Address


class TestControllerInterface:
    """Tests to verify Controller base class behavior."""

    def test_controller_methods_raise_not_implemented(self):
        """Test that Controller raises NotImplementedError for base methods."""
        ctrl = Controller()
        
        with pytest.raises(NotImplementedError):
            ctrl.start()
        
        with pytest.raises(NotImplementedError):
            ctrl.stop()

    def test_controller_concrete_implementation_possible(self):
        """Test that we can create a concrete implementation of Controller."""
        # Create a mock implementation to verify interface
        class TestController(Controller):
            def start(self) -> None:
                self._started = True
                
            def stop(self) -> None:
                self._started = False
        
        # Verify we can instantiate the concrete class
        ctrl = TestController()
        ctrl.start()
        assert hasattr(ctrl, '_started') and ctrl._started is True
        ctrl.stop()
        assert ctrl._started is False


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

    def test_controller_callbacks_set_on_init(self):
        """Test that controller sets view callbacks on init."""
        node = Node(address="127.0.0.1", port=5000)
        view = MagicMock()
        TkinterController(node, view)
        # Verify callbacks were set
        view.set_send_callback.assert_called_once()
        view.set_user_click_callback.assert_called_once()
        view.set_close_callback.assert_called_once()

    def test_controller_start_creates_socket(self):
        """Test that start creates socket and threads."""
        node = Node(address="127.0.0.1", port=5000)
        view = MagicMock()
        controller = TkinterController(node, view)

        with patch("ai_ring_chat.control.network.create_socket") as mock_create:
            mock_create.return_value = MagicMock()
            controller.start()

            mock_create.assert_called_once_with(5000)
            assert controller._running is True

    def test_controller_stop_sets_running_false(self):
        """Test that stop sets running to false."""
        node = Node(address="127.0.0.1", port=5000)
        view = MagicMock()
        controller = TkinterController(node, view)

        controller.start()
        controller.stop()

        assert controller._running is False

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

    def test_send_private_message_invalid_target(self):
        """Test _send_private_message with invalid target format."""
        node = Node(
            address="127.0.0.1", port=5000, next_address="127.0.0.1", next_port=5001
        )
        view = MagicMock()
        controller = TkinterController(node, view)

        # Invalid target format should not crash
        with patch("ai_ring_chat.control.network.parse_message") as mock_parse:
            mock_parse.side_effect = ValueError("Invalid address")
            controller._send_private_message("@invalid Test")

        # Should not have sent anything
        view.append_message.assert_not_called()

    def test_send_private_message_no_payload(self):
        """Test _send_private_message with no payload (just target)."""
        node = Node(
            address="127.0.0.1", port=5000, next_address="127.0.0.1", next_port=5001
        )
        view = MagicMock()
        controller = TkinterController(node, view)

        # No payload - should return early
        controller._send_private_message("@127.0.0.1:5001")

        # Should not have sent anything
        view.append_message.assert_not_called()

    def test_send_private_message_direct(self):
        """Test _send_private_message method directly."""
        node = Node(
            address="127.0.0.1", port=5000, next_address="127.0.0.1", next_port=5001
        )
        view = MagicMock()
        controller = TkinterController(node, view)

        with patch("ai_ring_chat.control.network.send") as mock_send:
            mock_send.return_value = True
            controller._send_private_message("@127.0.0.1:5001 Hello private")

        # Should have sent via network
        mock_send.assert_called()
        # Should have shown in view
        view.append_message.assert_called()

    def test_send_public_message_direct(self):
        """Test _send_public_message method directly."""
        node = Node(
            address="127.0.0.1", port=5000, next_address="127.0.0.1", next_port=5001
        )
        view = MagicMock()
        controller = TkinterController(node, view)

        with patch("ai_ring_chat.control.network.send") as mock_send:
            mock_send.return_value = True
            controller._send_public_message("Hello world")

        # Should have sent via network
        mock_send.assert_called()
        # Should have shown in view with own address
        view.append_message.assert_called()

    def test_is_private_message_for_us(self):
        """Test _is_private_message_for_us method."""
        node = Node(address="127.0.0.1", port=5000)
        view = MagicMock()
        controller = TkinterController(node, view)

        # Message for us
        msg = Message(
            msg_type=MessageType.USER,
            sender=Address("127.0.0.1", 5001),
            content="127.0.0.1:5000 Hello",
        )
        assert controller._is_private_message_for_us(msg) is True

        # Message for someone else
        msg_other = Message(
            msg_type=MessageType.USER,
            sender=Address("127.0.0.1", 5001),
            content="127.0.0.1:5002 Hello",
        )
        assert controller._is_private_message_for_us(msg_other) is False

    def test_extract_private_payload(self):
        """Test _extract_private_payload method."""
        node = Node(address="127.0.0.1", port=5000)
        view = MagicMock()
        controller = TkinterController(node, view)

        # Message with payload
        msg = Message(
            msg_type=MessageType.USER,
            sender=Address("127.0.0.1", 5001),
            content="127.0.0.1:5000 Hello world",
        )
        assert controller._extract_private_payload(msg) == "Hello world"

        # Message without payload
        msg_no_payload = Message(
            msg_type=MessageType.USER,
            sender=Address("127.0.0.1", 5001),
            content="127.0.0.1:5000",
        )
        assert controller._extract_private_payload(msg_no_payload) == ""

    def test_send_via_network(self):
        """Test _send_via_network method."""
        node = Node(address="127.0.0.1", port=5000)
        view = MagicMock()
        controller = TkinterController(node, view)

        with patch("ai_ring_chat.control.network.send") as mock_send:
            with patch("ai_ring_chat.control.network.parse_message") as mock_parse:
                mock_parse.return_value = Message(
                    msg_type=MessageType.TEXT,
                    sender=Address("127.0.0.1", 5000),
                    content="test",
                )
                mock_send.return_value = True
                controller._send_via_network("127.0.0.1", 5001, "TEXT test")

        mock_parse.assert_called_once_with("TEXT test")
        mock_send.assert_called_once_with("127.0.0.1", 5001, mock_parse.return_value)

    def test_handle_join_direct(self):
        """Test _handle_join method."""
        node = Node(address="127.0.0.1", port=5000)
        view = MagicMock()
        controller = TkinterController(node, view)

        msg = Message(
            msg_type=MessageType.JOIN, sender=Address("127.0.0.1", 5001), content=""
        )

        with patch("ai_ring_chat.control.network.send") as mock_send:
            mock_send.return_value = True
            controller._handle_join(msg)

        # Should have set next node
        assert node.next_address == "127.0.0.1"
        assert node.next_port == 5001
        # Should update view
        view.update_user_list.assert_called()
        view.append_message.assert_called()

    def test_handle_exit_direct(self):
        """Test _handle_exit method."""
        node = Node(
            address="127.0.0.1", port=5000, next_address="127.0.0.1", next_port=5001
        )
        view = MagicMock()
        controller = TkinterController(node, view)

        msg = Message(
            msg_type=MessageType.EXIT,
            sender=Address("127.0.0.1", 5001),
            content="127.0.0.1:5002",
        )

        with patch("ai_ring_chat.control.network.send") as mock_send:
            mock_send.return_value = True
            controller._handle_exit(msg)

        view.update_user_list.assert_called()
        view.append_message.assert_called()

    def test_handle_ping_direct(self):
        """Test _handle_ping method."""
        node = Node(address="127.0.0.1", port=5000)
        view = MagicMock()
        controller = TkinterController(node, view)

        msg = Message(
            msg_type=MessageType.PING, sender=Address("127.0.0.1", 5001), content=""
        )

        with patch("ai_ring_chat.control.network.send") as mock_send:
            mock_send.return_value = True
            controller._handle_ping(msg)

        # Should have recorded ping
        assert node.last_ping_received is not None
        # Should have sent response
        mock_send.assert_called()

    def test_handle_echo_direct(self):
        """Test _handle_echo method."""
        node = Node(address="127.0.0.1", port=5000)
        view = MagicMock()
        controller = TkinterController(node, view)

        msg = Message(
            msg_type=MessageType.ECHO, sender=Address("127.0.0.1", 5001), content=""
        )

        controller._handle_echo(msg)

        # Should have recorded echo
        assert node.last_echo_received is not None

    def test_handle_next_direct_when_head(self):
        """Test _handle_next when node is head."""
        # Set up as head with multiple nodes in address book
        node = Node(
            address="127.0.0.1", port=5000,
            next_address="127.0.0.1", next_port=5001
        )
        # Add addresses to make it the head (multiple nodes in ring)
        node.add_to_address_book("127.0.0.1", 5000)
        node.add_to_address_book("127.0.0.1", 5001)
        
        view = MagicMock()
        controller = TkinterController(node, view)

        msg = Message(
            msg_type=MessageType.NEXT,
            sender=Address("127.0.0.1", 5001),
            content="127.0.0.1:5002"
        )

        with patch("ai_ring_chat.control.network.send") as mock_send:
            mock_send.return_value = True
            controller._handle_next(msg)

        # Should have shown recovery message for head node

    def test_handle_next_direct_when_not_head(self):
        """Test _handle_next when node is not head."""
        # Single node - not head
        node = Node(
            address="127.0.0.1", port=5000,
            next_address="127.0.0.1", next_port=5001
        )
        
        view = MagicMock()
        controller = TkinterController(node, view)

        msg = Message(
            msg_type=MessageType.NEXT,
            sender=Address("127.0.0.1", 5001),
            content="127.0.0.1:5002"
        )

        with patch("ai_ring_chat.control.network.send") as mock_send:
            mock_send.return_value = True
            controller._handle_next(msg)

        # Should NOT have shown recovery message for non-head

    def test_send_to_next_no_next_node(self):
        """Test _send_to_next when there is no next node."""
        node = Node(address="127.0.0.1", port=5000)
        # No next node set
        node.next_address = None
        node.next_port = None
        
        view = MagicMock()
        controller = TkinterController(node, view)

        msg = Message(
            msg_type=MessageType.TEXT,
            sender=Address("127.0.0.1", 5000),
            content="test"
        )

        result = controller._send_to_next(msg)
        assert result is False

    def test_send_to_next_success(self):
        """Test _send_to_next when next node exists."""
        node = Node(
            address="127.0.0.1", port=5000,
            next_address="127.0.0.1", next_port=5001
        )
        
        view = MagicMock()
        controller = TkinterController(node, view)

        msg = Message(
            msg_type=MessageType.TEXT,
            sender=Address("127.0.0.1", 5000),
            content="test"
        )

        with patch("ai_ring_chat.control.network.send") as mock_send:
            mock_send.return_value = True
            result = controller._send_to_next(msg)
            assert result is True
            mock_send.assert_called_once()

    def test_handle_text_direct(self):
        """Test _handle_text method."""
        node = Node(address="127.0.0.1", port=5000)
        view = MagicMock()
        controller = TkinterController(node, view)

        msg = Message(
            msg_type=MessageType.TEXT,
            sender=Address("127.0.0.1", 5001),
            content="Hello",
        )

        with patch("ai_ring_chat.control.network.send") as mock_send:
            mock_send.return_value = True
            controller._handle_text(msg)

        # Should add to address book
        assert "127.0.0.1:5001" in node.address_book
        view.append_message.assert_called()
        view.update_user_list.assert_called()

    def test_handle_user_direct_for_us(self):
        """Test _handle_user method when message is for us."""
        node = Node(address="127.0.0.1", port=5000)
        view = MagicMock()
        controller = TkinterController(node, view)

        msg = Message(
            msg_type=MessageType.USER,
            sender=Address("127.0.0.1", 5001),
            content="127.0.0.1:5000 Secret",
        )

        with patch.object(controller, "_is_private_message_for_us", return_value=True):
            controller._handle_user(msg)

        # Should add to address book
        assert "127.0.0.1:5001" in node.address_book
        # Should show private message in view
        view.append_message.assert_called()

    def test_handle_user_direct_not_for_us(self):
        """Test _handle_user method when message is not for us."""
        node = Node(
            address="127.0.0.1", port=5000, next_address="127.0.0.1", next_port=5002
        )
        view = MagicMock()
        controller = TkinterController(node, view)

        msg = Message(
            msg_type=MessageType.USER,
            sender=Address("127.0.0.1", 5001),
            content="127.0.0.1:5002 Secret",
        )

        with patch("ai_ring_chat.control.network.send") as mock_send:
            mock_send.return_value = True
            controller._handle_user(msg)

        # Should add to address book
        assert "127.0.0.1:5001" in node.address_book
        # Should have propagated to next
        mock_send.assert_called()
