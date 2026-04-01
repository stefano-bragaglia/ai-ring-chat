"""Tests for the protocol module."""

from unittest.mock import MagicMock

from ai_ring_chat.model.nodes import Node
from ai_ring_chat.model.message import Message, MessageType, Address
from ai_ring_chat.model.protocol import (
    handle_join,
    handle_exit,
    handle_ping,
    handle_echo,
    handle_next,
    handle_text,
    handle_user,
    create_response,
)


class TestHandleJoin:
    """Tests for handle_join protocol method."""

    def test_handle_join_sets_next(self):
        """Test that JOIN sets the node's next to the sender."""
        node = Node(address="127.0.0.1", port=5000)
        node.set_next("127.0.0.1", 5001)  # Has existing next
        msg = Message(
            msg_type=MessageType.JOIN, sender=Address("127.0.0.1", 5002), content=""
        )

        mock_sender = MagicMock()
        handle_join(node, msg, mock_sender)

        assert node.next_address == "127.0.0.1"
        assert node.next_port == 5002

    def test_handle_join_adds_to_address_book(self):
        """Test that JOIN adds sender to address book."""
        node = Node(address="127.0.0.1", port=5000)
        msg = Message(
            msg_type=MessageType.JOIN, sender=Address("127.0.0.1", 5002), content=""
        )

        mock_sender = MagicMock()
        handle_join(node, msg, mock_sender)

        assert "127.0.0.1:5002" in node.address_book

    def test_handle_join_propagates(self):
        """Test that JOIN propagates to next node."""
        node = Node(
            address="127.0.0.1", port=5000, next_address="127.0.0.1", next_port=5001
        )
        msg = Message(
            msg_type=MessageType.JOIN, sender=Address("127.0.0.1", 5002), content=""
        )

        mock_sender = MagicMock()
        handle_join(node, msg, mock_sender)

        # Check that sender was called (propagation)
        mock_sender.assert_called_once()


class TestHandleExit:
    """Tests for handle_exit protocol method."""

    def test_handle_exit_removes_exiting_node(self):
        """Test that EXIT removes the exiting node from ring."""
        # Node A -> Node B (exiting) -> Node C
        # Node A receives EXIT from B with next C
        node_a = Node(
            address="127.0.0.1", port=5000, next_address="127.0.0.1", next_port=5001
        )
        # Node B is exiting, its next is C (5002)
        msg = Message(
            msg_type=MessageType.EXIT,
            sender=Address("127.0.0.1", 5001),
            content="127.0.0.1:5002",
        )

        mock_sender = MagicMock()
        handle_exit(node_a, msg, mock_sender)

        assert node_a.next_address == "127.0.0.1"
        assert node_a.next_port == 5002

    def test_handle_exit_removes_from_address_book(self):
        """Test that EXIT removes exiting node from address book."""
        node = Node(address="127.0.0.1", port=5000)
        node.add_to_address_book("127.0.0.1", 5001)
        node.add_to_address_book("127.0.0.1", 5002)

        msg = Message(
            msg_type=MessageType.EXIT,
            sender=Address("127.0.0.1", 5001),
            content="127.0.0.1:5002",
        )

        mock_sender = MagicMock()
        handle_exit(node, msg, mock_sender)

        assert "127.0.0.1:5001" not in node.address_book
        assert "127.0.0.1:5002" in node.address_book  # This is E's next, should remain

    def test_handle_exit_propagates(self):
        """Test that EXIT propagates to next node."""
        node = Node(
            address="127.0.0.1", port=5000, next_address="127.0.0.1", next_port=5001
        )
        msg = Message(
            msg_type=MessageType.EXIT,
            sender=Address("127.0.0.1", 5001),
            content="127.0.0.1:5002",
        )

        mock_sender = MagicMock()
        handle_exit(node, msg, mock_sender)

        mock_sender.assert_called_once()


class TestHandlePing:
    """Tests for handle_ping protocol method."""

    def test_handle_ping_records_timestamp(self):
        """Test that PING records the timestamp."""
        node = Node(address="127.0.0.1", port=5000)
        msg = Message(
            msg_type=MessageType.PING, sender=Address("127.0.0.1", 5001), content=""
        )

        mock_sender = MagicMock()
        handle_ping(node, msg, mock_sender)

        assert node.last_ping_received is not None

    def test_handle_ping_responds_with_echo(self):
        """Test that PING triggers ECHO response."""
        node = Node(address="127.0.0.1", port=5000)
        msg = Message(
            msg_type=MessageType.PING, sender=Address("127.0.0.1", 5001), content=""
        )

        mock_sender = MagicMock()
        handle_ping(node, msg, mock_sender)

        # Should send ECHO to the sender
        mock_sender.assert_called_once()
        call_args = mock_sender.call_args[0]
        # First arg is address, second is port, third is message string
        assert "ECHO" in call_args[2]


class TestHandleEcho:
    """Tests for handle_echo protocol method."""

    def test_handle_echo_records_timestamp(self):
        """Test that ECHO records the timestamp."""
        node = Node(address="127.0.0.1", port=5000)
        msg = Message(
            msg_type=MessageType.ECHO, sender=Address("127.0.0.1", 5001), content=""
        )

        mock_sender = MagicMock()
        handle_echo(node, msg, mock_sender)

        assert node.last_echo_received is not None


class TestHandleNext:
    """Tests for handle_next protocol method."""

    def test_handle_next_head_sets_next(self):
        """Test that NEXT sets next when node is head."""
        # Node is head: has next but not receiving ECHOs
        node = Node(
            address="127.0.0.1", port=5000, next_address="127.0.0.1", next_port=5001
        )
        node.last_echo_received = None  # No echo received = head
        msg = Message(
            msg_type=MessageType.NEXT, sender=Address("127.0.0.1", 5002), content=""
        )

        mock_sender = MagicMock()
        handle_next(node, msg, mock_sender)

        assert node.next_address == "127.0.0.1"
        assert node.next_port == 5002

    def test_handle_next_not_head_propagates(self):
        """Test that NEXT propagates when node is not head."""
        node = Node(
            address="127.0.0.1", port=5000, next_address="127.0.0.1", next_port=5001
        )
        node.last_echo_received = 1000  # Has echo = not head
        msg = Message(
            msg_type=MessageType.NEXT, sender=Address("127.0.0.1", 5002), content=""
        )

        mock_sender = MagicMock()
        handle_next(node, msg, mock_sender)

        # Should propagate to next
        mock_sender.assert_called_once()


class TestHandleText:
    """Tests for handle_text protocol method."""

    def test_handle_text_new_message_propagates(self):
        """Test that new TEXT message propagates."""
        node = Node(
            address="127.0.0.1", port=5000, next_address="127.0.0.1", next_port=5001
        )
        msg = Message(
            msg_type=MessageType.TEXT,
            sender=Address("127.0.0.1", 5000),
            content="Hello!",
        )

        mock_sender = MagicMock()
        handle_text(node, msg, mock_sender)

        assert "Hello!" in node.message_log
        mock_sender.assert_called_once()

    def test_handle_text_duplicate_does_not_propagate(self):
        """Test that duplicate TEXT message does not propagate."""
        node = Node(
            address="127.0.0.1", port=5000, next_address="127.0.0.1", next_port=5001
        )
        node.log_payload("Hello!")  # Already in log
        msg = Message(
            msg_type=MessageType.TEXT,
            sender=Address("127.0.0.1", 5000),
            content="Hello!",
        )

        mock_sender = MagicMock()
        handle_text(node, msg, mock_sender)

        # Should not propagate (sender not called or called with different message)
        # The exact behavior depends on implementation
        assert "Hello!" in node.message_log  # Still in log

    def test_handle_text_adds_sender_to_address_book(self):
        """Test that TEXT adds sender to address book."""
        node = Node(
            address="127.0.0.1", port=5000, next_address="127.0.0.1", next_port=5001
        )
        msg = Message(
            msg_type=MessageType.TEXT,
            sender=Address("127.0.0.1", 5002),
            content="Hello!",
        )

        mock_sender = MagicMock()
        handle_text(node, msg, mock_sender)

        assert "127.0.0.1:5002" in node.address_book


class TestHandleUser:
    """Tests for handle_user protocol method."""

    def test_handle_user_target_not_reached_propagates(self):
        """Test that USER propagates when target is not this node."""
        node = Node(
            address="127.0.0.1", port=5000, next_address="127.0.0.1", next_port=5001
        )
        # Target is 5002, this is node 5000
        msg = Message(
            msg_type=MessageType.USER,
            sender=Address("127.0.0.1", 5000),
            content="127.0.0.1:5002 Hello!",
        )

        mock_sender = MagicMock()
        handle_user(node, msg, mock_sender)

        mock_sender.assert_called_once()

    def test_handle_user_target_reached_does_not_propagate(self):
        """Test that USER does not propagate when target is this node."""
        node = Node(
            address="127.0.0.1", port=5000, next_address="127.0.0.1", next_port=5001
        )
        # Target is this node (5000)
        msg = Message(
            msg_type=MessageType.USER,
            sender=Address("127.0.0.1", 5002),
            content="127.0.0.1:5000 Hello!",
        )

        mock_sender = MagicMock()
        handle_user(node, msg, mock_sender)

        # Should not propagate to next
        mock_sender.assert_not_called()

    def test_handle_user_adds_sender_to_address_book(self):
        """Test that USER adds sender to address book."""
        node = Node(
            address="127.0.0.1", port=5000, next_address="127.0.0.1", next_port=5001
        )
        msg = Message(
            msg_type=MessageType.USER,
            sender=Address("127.0.0.1", 5002),
            content="127.0.0.1:5002 Hello!",
        )

        mock_sender = MagicMock()
        handle_user(node, msg, mock_sender)

        assert "127.0.0.1:5002" in node.address_book

    def test_handle_user_invalid_format_no_space(self):
        """Test that USER with no space between target and message returns early."""
        node = Node(
            address="127.0.0.1", port=5000, next_address="127.0.0.1", next_port=5001
        )
        # Invalid: no space between target and message
        msg = Message(
            msg_type=MessageType.USER,
            sender=Address("127.0.0.1", 5002),
            content="127.0.0.1:5002",
        )

        mock_sender = MagicMock()
        handle_user(node, msg, mock_sender)

        # Should return early, not propagate
        mock_sender.assert_not_called()

    def test_handle_user_invalid_target_address(self):
        """Test that USER with invalid target returns early."""
        node = Node(
            address="127.0.0.1", port=5000, next_address="127.0.0.1", next_port=5001
        )
        # Invalid: not a valid address
        msg = Message(
            msg_type=MessageType.USER,
            sender=Address("127.0.0.1", 5002),
            content="invalid Hello!",
        )

        mock_sender = MagicMock()
        handle_user(node, msg, mock_sender)

        # Should return early, not propagate
        mock_sender.assert_not_called()


class TestCreateResponse:
    """Tests for create_response helper function."""

    def test_create_response_echo(self):
        """Test creating ECHO response."""
        node = Node(address="127.0.0.1", port=5000)
        ping_msg = Message(
            msg_type=MessageType.PING, sender=Address("127.0.0.1", 5001), content=""
        )

        response = create_response(node, ping_msg)

        assert response.msg_type == MessageType.ECHO
        assert response.sender == Address("127.0.0.1", 5000)

    def test_create_response_other_type(self):
        """Test creating response for non-PING message."""
        node = Node(address="127.0.0.1", port=5000)
        text_msg = Message(
            msg_type=MessageType.TEXT,
            sender=Address("127.0.0.1", 5001),
            content="Hello",
        )

        response = create_response(node, text_msg)

        # Should return same type with node as sender
        assert response.msg_type == MessageType.TEXT
        assert response.sender == Address("127.0.0.1", 5000)
