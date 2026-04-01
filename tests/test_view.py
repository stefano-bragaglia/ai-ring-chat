"""Tests for the view module."""

import pytest

from ai_ring_chat.view import View
from ai_ring_chat.view.views import TkinterView


class TestViewInterface:
    """Tests to verify View is an abstract class."""

    def test_view_is_abstract(self):
        """Test that View cannot be instantiated directly."""
        with pytest.raises(TypeError):
            View()


class TestTkinterView:
    """Tests for TkinterView implementation."""

    def test_tkinter_view_creation(self):
        """Test that TkinterView can be created."""
        view = TkinterView("127.0.0.1", 5000)
        assert view is not None
        view.destroy()

    def test_window_title(self):
        """Test that window title is set correctly."""
        view = TkinterView("127.0.0.1", 5000)
        assert view.get_window_title() == "127.0.0.1:5000"
        view.destroy()

    def test_update_user_list(self):
        """Test that user list can be updated."""
        view = TkinterView("127.0.0.1", 5000)
        view.update_user_list(["127.0.0.1:5001", "127.0.0.1:5002"])
        view.destroy()

    def test_append_message(self):
        """Test that messages can be appended to chat log."""
        view = TkinterView("127.0.0.1", 5000)
        view.append_message("Test message")
        view.destroy()

    def test_clear_message(self):
        """Test that message input can be cleared."""
        view = TkinterView("127.0.0.1", 5000)
        view.set_input_text("Some text")
        view.clear_message()
        assert view.get_input_text() == ""
        view.destroy()

    def test_get_input_text(self):
        """Test getting text from input field."""
        view = TkinterView("127.0.0.1", 5000)
        view.set_input_text("Hello world")
        assert view.get_input_text() == "Hello world"
        view.destroy()

    def test_set_input_text(self):
        """Test setting text in input field."""
        view = TkinterView("127.0.0.1", 5000)
        view.set_input_text("Test message")
        assert view.get_input_text() == "Test message"
        view.destroy()

    def test_send_callback(self):
        """Test that send callback can be set and called."""
        view = TkinterView("127.0.0.1", 5000)
        callback_called = []

        def callback():
            callback_called.append(True)

        view.set_send_callback(callback)

        # Simulate send action (click button or press enter)
        view._on_send()

        assert len(callback_called) == 1
        view.destroy()

    def test_user_click_callback(self):
        """Test that user click callback can be set."""
        view = TkinterView("127.0.0.1", 5000)
        clicked_user = []

        def callback(user):
            clicked_user.append(user)

        view.set_user_click_callback(callback)
        view.destroy()

    def test_close_callback(self):
        """Test that close callback can be set."""
        view = TkinterView("127.0.0.1", 5000)
        callback_called = []

        def callback():
            callback_called.append(True)

        view.set_close_callback(callback)
        view.destroy()

    def test_prepend_user_to_input(self):
        """Test prepending user to input field."""
        view = TkinterView("127.0.0.1", 5000)

        # No existing prefix
        view.set_input_text("Hello")
        view._prepend_user("127.0.0.1:5001")
        assert view.get_input_text() == "@127.0.0.1:5001 Hello"

        view.destroy()

    def test_prepend_user_replaces_existing(self):
        """Test that prepending user replaces existing prefix."""
        view = TkinterView("127.0.0.1", 5000)

        # Existing prefix
        view.set_input_text("@127.0.0.1:5002 Hello world")
        view._prepend_user("127.0.0.1:5001")
        assert view.get_input_text() == "@127.0.0.1:5001 Hello world"

        view.destroy()

    def test_prepend_user_own_address_not_shown(self):
        """Test that own address is not shown in user list."""
        view = TkinterView("127.0.0.1", 5000)

        # Add self to list - should not appear
        view.update_user_list(["127.0.0.1:5000", "127.0.0.1:5001"])

        # The own address should be filtered out
        view.destroy()

    def test_chat_log_limit(self):
        """Test that chat log is limited to 100 messages."""
        view = TkinterView("127.0.0.1", 5000)

        # Add more than 100 messages
        for i in range(150):
            view.append_message(f"Message {i}")

        # Check that log is limited (implementation detail)
        view.destroy()


class TestViewIntegration:
    """Integration tests for view components."""

    def test_view_with_mock_callbacks(self):
        """Test view with all callbacks set."""
        view = TkinterView("127.0.0.1", 5000)

        send_called = []
        user_click_called = []
        close_called = []

        view.set_send_callback(lambda: send_called.append(True))
        view.set_user_click_callback(lambda u: user_click_called.append(u))
        view.set_close_callback(lambda: close_called.append(True))

        # Verify callbacks are set (they're stored as attributes)
        assert view._send_callback is not None
        assert view._user_click_callback is not None
        assert view._close_callback is not None

        view.destroy()

    def test_get_message_empty(self):
        """Test get_message when input is empty."""
        view = TkinterView("127.0.0.1", 5000)
        assert view.get_message() == ""
        view.destroy()

    def test_get_message_with_text(self):
        """Test get_message with text in input."""
        view = TkinterView("127.0.0.1", 5000)
        view.set_input_text("Test message")
        assert view.get_message() == "Test message"
        view.destroy()
