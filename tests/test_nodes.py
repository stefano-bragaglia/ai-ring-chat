"""Tests for the Node data model."""

from ai_ring_chat.model.nodes import Node


class TestNodeCreation:
    """Tests for Node initialization."""

    def test_create_node_with_address_and_port(self):
        """Test creating a node with address and port."""
        node = Node(address="127.0.0.1", port=5000)
        assert node.address == "127.0.0.1"
        assert node.port == 5000

    def test_create_node_with_optional_next(self):
        """Test creating a node with next node address."""
        node = Node(
            address="127.0.0.1", port=5000, next_address="127.0.0.1", next_port=5001
        )
        assert node.next_address == "127.0.0.1"
        assert node.next_port == 5001

    def test_create_node_with_empty_address_book(self):
        """Test that node starts with empty address book."""
        node = Node(address="127.0.0.1", port=5000)
        assert node.address_book == []

    def test_create_node_with_empty_message_log(self):
        """Test that node starts with empty message log."""
        node = Node(address="127.0.0.1", port=5000)
        assert node.message_log == []


class TestSetNext:
    """Tests for set_next method."""

    def test_set_next_node(self):
        """Test setting the next node in the ring."""
        node = Node(address="127.0.0.1", port=5000)
        node.set_next("127.0.0.1", 5001)
        assert node.next_address == "127.0.0.1"
        assert node.next_port == 5001

    def test_set_next_overwrites_previous(self):
        """Test that set_next overwrites previous next node."""
        node = Node(
            address="127.0.0.1", port=5000, next_address="127.0.0.1", next_port=5001
        )
        node.set_next("127.0.0.1", 5002)
        assert node.next_address == "127.0.0.1"
        assert node.next_port == 5002


class TestRemoveNext:
    """Tests for remove_next method."""

    def test_remove_next_clears_next_node(self):
        """Test that remove_next clears the next node."""
        node = Node(
            address="127.0.0.1", port=5000, next_address="127.0.0.1", next_port=5001
        )
        node.remove_next()
        assert node.next_address is None
        assert node.next_port is None

    def test_remove_next_when_no_next(self):
        """Test that remove_next works when there's no next node."""
        node = Node(address="127.0.0.1", port=5000)
        node.remove_next()  # Should not raise
        assert node.next_address is None
        assert node.next_port is None


class TestAddToAddressBook:
    """Tests for add_to_address_book method."""

    def test_add_single_address(self):
        """Test adding a single address to the address book."""
        node = Node(address="127.0.0.1", port=5000)
        node.add_to_address_book("127.0.0.1", 5001)
        assert len(node.address_book) == 1

    def test_add_multiple_addresses_sorted(self):
        """Test that addresses are stored in alphabetical order."""
        node = Node(address="127.0.0.1", port=5000)
        node.add_to_address_book("127.0.0.2", 5002)
        node.add_to_address_book("127.0.0.1", 5001)
        assert node.address_book == [
            "127.0.0.1:5001",
            "127.0.0.2:5002",
        ]

    def test_add_duplicate_address_not_added(self):
        """Test that duplicate addresses are not added."""
        node = Node(address="127.0.0.1", port=5000)
        node.add_to_address_book("127.0.0.1", 5001)
        node.add_to_address_book("127.0.0.1", 5001)
        assert len(node.address_book) == 1

    def test_does_not_add_self(self):
        """Test that node does not add itself to address book."""
        node = Node(address="127.0.0.1", port=5000)
        node.add_to_address_book("127.0.0.1", 5000)
        assert len(node.address_book) == 0


class TestRemoveFromAddressBook:
    """Tests for remove_from_address_book method."""

    def test_remove_existing_address(self):
        """Test removing an existing address from address book."""
        node = Node(address="127.0.0.1", port=5000)
        node.add_to_address_book("127.0.0.1", 5001)
        node.add_to_address_book("127.0.0.2", 5002)
        node.remove_from_address_book("127.0.0.1", 5001)
        assert node.address_book == ["127.0.0.2:5002"]

    def test_remove_nonexistent_address(self):
        """Test that removing nonexistent address does nothing."""
        node = Node(address="127.0.0.1", port=5000)
        node.add_to_address_book("127.0.0.1", 5001)
        node.remove_from_address_book("127.0.0.2", 5002)
        assert node.address_book == ["127.0.0.1:5001"]


class TestLogPayload:
    """Tests for log_payload method."""

    def test_log_single_payload(self):
        """Test logging a single payload."""
        node = Node(address="127.0.0.1", port=5000)
        node.log_payload("Hello!")
        assert node.message_log == ["Hello!"]

    def test_log_multiple_payloads(self):
        """Test logging multiple payloads."""
        node = Node(address="127.0.0.1", port=5000)
        node.log_payload("Hello!")
        node.log_payload("World!")
        node.log_payload("Test")
        assert node.message_log == ["Hello!", "World!", "Test"]

    def test_log_duplicate_payload(self):
        """Test that duplicate payloads are not added."""
        node = Node(address="127.0.0.1", port=5000)
        node.log_payload("Hello!")
        node.log_payload("Hello!")
        assert node.message_log == ["Hello!"]


class TestClearMessageLog:
    """Tests for clear_message_log method."""

    def test_clear_message_log(self):
        """Test clearing the message log."""
        node = Node(address="127.0.0.1", port=5000)
        node.log_payload("Hello!")
        node.log_payload("World!")
        node.clear_message_log()
        assert node.message_log == []


class TestIsSingleNode:
    """Tests for is_single_node property."""

    def test_single_node_has_no_next(self):
        """Test that a node with no next is a single node."""
        node = Node(address="127.0.0.1", port=5000)
        assert node.is_single_node is True

    def test_not_single_node_has_next(self):
        """Test that a node with next is not a single node."""
        node = Node(
            address="127.0.0.1", port=5000, next_address="127.0.0.1", next_port=5001
        )
        assert node.is_single_node is False


class TestAddressBookEntryRemoval:
    """Tests for removing addresses from address book on exit."""

    def test_remove_self_on_exit(self):
        """Test that node removes itself from its own address book on exit."""
        node = Node(address="127.0.0.1", port=5000)
        node.add_to_address_book("127.0.0.1", 5000)  # Self added (shouldn't be)
        node.add_to_address_book("127.0.0.2", 5002)
        # Node on exit removes itself from address book
        node.remove_from_address_book("127.0.0.1", 5000)
        # Self was never added (add_to_address_book skips self)
        assert "127.0.0.1:5000" not in node.address_book


class TestAddressProperties:
    """Tests for address string properties."""

    def test_self_address_str(self):
        """Test the self_address_str property."""
        node = Node(address="127.0.0.1", port=5000)
        assert node.self_address_str == "127.0.0.1:5000"

    def test_next_address_str_when_set(self):
        """Test next_address_str when next is set."""
        node = Node(
            address="127.0.0.1", port=5000, next_address="127.0.0.1", next_port=5001
        )
        assert node.next_address_str == "127.0.0.1:5001"

    def test_next_address_str_when_none(self):
        """Test next_address_str when next is None."""
        node = Node(address="127.0.0.1", port=5000)
        assert node.next_address_str is None
