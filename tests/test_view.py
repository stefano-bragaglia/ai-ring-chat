"""Tests for the view module."""

import pytest
from unittest.mock import MagicMock, patch

from ai_ring_chat.view.views import View, TkinterView


class MockView(View):
    """Concrete implementation of View for testing."""

    def __init__(self):
        self._users = []
        self._messages = []
        self._input_text = ""
        self._send_cb = None
        self._user_click_cb = None
        self._close_cb = None

    def show(self) -> None:
        pass

    def update_user_list(self, users: list[str]) -> None:
        self._users = users

    def append_message(self, message: str) -> None:
        self._messages.append(message)

    def get_message(self) -> str:
        return self._input_text

    def clear_message(self) -> None:
        self._input_text = ""

    def set_send_callback(self, callback) -> None:
        self._send_cb = callback

    def set_user_click_callback(self, callback) -> None:
        self._user_click_cb = callback

    def set_close_callback(self, callback) -> None:
        self._close_cb = callback

    def set_input_text(self, text: str) -> None:
        self._input_text = text


class TestViewInterface:
    """Tests to verify View base class behavior."""

    def test_view_methods_raise_not_implemented(self):
        """Test that View raises NotImplementedError for base methods."""
        view = View()
        
        with pytest.raises(NotImplementedError):
            view.show()
        
        with pytest.raises(NotImplementedError):
            view.update_user_list([])
        
        with pytest.raises(NotImplementedError):
            view.append_message("")
        
        with pytest.raises(NotImplementedError):
            view.get_message()
        
        with pytest.raises(NotImplementedError):
            view.clear_message()
        
        with pytest.raises(NotImplementedError):
            view.set_send_callback(lambda: None)
        
        with pytest.raises(NotImplementedError):
            view.set_user_click_callback(lambda u: None)
        
        with pytest.raises(NotImplementedError):
            view.set_close_callback(lambda: None)
        
        with pytest.raises(NotImplementedError):
            view.set_input_text("")

    def test_mock_view_is_concrete(self):
        """Test that MockView can be instantiated."""
        view = MockView()
        assert view is not None
        # Should be able to call all methods without error
        view.show()
        view.update_user_list(["user1"])
        view.append_message("test")
        view.get_message()
        view.clear_message()
        view.set_send_callback(lambda: None)
        view.set_user_click_callback(lambda u: None)
        view.set_close_callback(lambda: None)
        view.set_input_text("test")

    def test_view_abstract_methods_exist(self):
        """Test that View class has all expected abstract methods."""
        # Check that all abstract methods exist in View class
        assert hasattr(View, "show")
        assert hasattr(View, "update_user_list")
        assert hasattr(View, "append_message")
        assert hasattr(View, "get_message")
        assert hasattr(View, "clear_message")
        assert hasattr(View, "set_send_callback")
        assert hasattr(View, "set_user_click_callback")
        assert hasattr(View, "set_close_callback")
        assert hasattr(View, "set_input_text")

    def test_abstract_methods_are_callable(self):
        """Test that MockView implements all View abstract methods."""
        view = MockView()
        # Call each method to verify implementation exists
        view.show()
        view.update_user_list([])
        view.append_message("")
        _ = view.get_message()
        view.clear_message()
        view.set_send_callback(lambda: None)
        view.set_user_click_callback(lambda u: None)
        view.set_close_callback(lambda: None)
        view.set_input_text("")

    def test_view_show_method(self):
        """Test View.show abstract method exists."""
        # Verify the method exists and is abstract
        assert hasattr(View, 'show')
        # Verify it's callable via MockView
        view = MockView()
        view.show()  # Should not raise

    def test_view_update_user_list_method(self):
        """Test View.update_user_list abstract method exists."""
        assert hasattr(View, 'update_user_list')
        view = MockView()
        view.update_user_list(["user1", "user2"])
        assert view._users == ["user1", "user2"]

    def test_view_append_message_method(self):
        """Test View.append_message abstract method exists."""
        assert hasattr(View, 'append_message')
        view = MockView()
        view.append_message("Hello")
        assert "Hello" in view._messages

    def test_view_get_message_method(self):
        """Test View.get_message abstract method exists."""
        assert hasattr(View, 'get_message')
        view = MockView()
        view._input_text = "Test message"
        assert view.get_message() == "Test message"

    def test_view_clear_message_method(self):
        """Test View.clear_message abstract method exists."""
        assert hasattr(View, 'clear_message')
        view = MockView()
        view._input_text = "Some text"
        view.clear_message()
        assert view._input_text == ""

    def test_view_set_send_callback_method(self):
        """Test View.set_send_callback abstract method exists."""
        assert hasattr(View, 'set_send_callback')
        view = MockView()
        
        def cb():
            pass
        view.set_send_callback(cb)
        assert view._send_cb is cb

    def test_view_set_user_click_callback_method(self):
        """Test View.set_user_click_callback abstract method exists."""
        assert hasattr(View, 'set_user_click_callback')
        view = MockView()
        
        def cb(u):
            pass
        view.set_user_click_callback(cb)
        assert view._user_click_cb is cb

    def test_view_set_close_callback_method(self):
        """Test View.set_close_callback abstract method exists."""
        assert hasattr(View, 'set_close_callback')
        view = MockView()
        
        def cb():
            pass
        view.set_close_callback(cb)
        assert view._close_cb is cb

    def test_view_set_input_text_method(self):
        """Test View.set_input_text abstract method exists."""
        assert hasattr(View, 'set_input_text')
        view = MockView()
        view.set_input_text("New text")
        assert view._input_text == "New text"


class TestTkinterView:
    """Tests for TkinterView implementation using mocks."""

    def test_tkinter_view_creation(self):
        """Test that TkinterView can be created."""
        with patch("ai_ring_chat.view.views.tk.Tk"):
            view = TkinterView("127.0.0.1", 5000)
            assert view is not None
            view.destroy()

    def test_tkinter_view_show_method(self):
        """Test that TkinterView.show calls mainloop."""
        with patch("ai_ring_chat.view.views.tk.Tk") as mock_tk:
            mock_root = MagicMock()
            mock_tk.return_value = mock_root
            view = TkinterView("127.0.0.1", 5000)
            view.show()
            mock_root.mainloop.assert_called_once()
            view.destroy()

    def test_tkinter_view_destroy(self):
        """Test that TkinterView.destroy works."""
        with patch("ai_ring_chat.view.views.tk.Tk") as mock_tk:
            mock_root = MagicMock()
            mock_tk.return_value = mock_root
            view = TkinterView("127.0.0.1", 5000)
            view.destroy()
            mock_root.destroy.assert_called_once()

    def test_tkinter_view_destroy_without_root(self):
        """Test destroy handles missing _root gracefully."""
        with patch("ai_ring_chat.view.views.tk.Tk"):
            view = TkinterView("127.0.0.1", 5000)
            del view._root
            # Should not raise
            view.destroy()

    def test_window_title(self):
        """Test that window title is set correctly."""
        with patch("ai_ring_chat.view.views.tk.Tk"):
            view = TkinterView("127.0.0.1", 5000)
            assert view.get_window_title() == "127.0.0.1:5000"
            view.destroy()

    def test_update_user_list(self):
        """Test that user list can be updated."""
        with patch("ai_ring_chat.view.views.tk.Tk"):
            view = TkinterView("127.0.0.1", 5000)
            # Mock the listbox
            view._user_listbox = MagicMock()
            view.update_user_list(["127.0.0.1:5001", "127.0.0.1:5002"])
            view._user_listbox.delete.assert_called()
            view._user_listbox.insert.assert_called()
            view.destroy()

    def test_append_message(self):
        """Test that messages can be appended to chat log."""
        with patch("ai_ring_chat.view.views.tk.Tk"):
            view = TkinterView("127.0.0.1", 5000)
            # Mock the text widget
            view._chat_text = MagicMock()
            view.append_message("Test message")
            assert "Test message" in view._chat_log
            view.destroy()

    def test_clear_message(self):
        """Test that message input can be cleared."""
        with patch("ai_ring_chat.view.views.tk.Tk"):
            view = TkinterView("127.0.0.1", 5000)
            # Mock the entry widget
            view._message_input = MagicMock()
            view.set_input_text("Some text")
            view.clear_message()
            view._message_input.delete.assert_called()
            view.destroy()

    def test_get_input_text(self):
        """Test getting text from input field."""
        with patch("ai_ring_chat.view.views.tk.Tk"):
            view = TkinterView("127.0.0.1", 5000)
            view._message_input = MagicMock()
            view._message_input.get.return_value = "Hello world"
            assert view.get_input_text() == "Hello world"
            view.destroy()

    def test_set_input_text(self):
        """Test setting text in input field."""
        with patch("ai_ring_chat.view.views.tk.Tk"):
            view = TkinterView("127.0.0.1", 5000)
            view._message_input = MagicMock()
            view.set_input_text("Test message")
            view._message_input.delete.assert_called()
            view._message_input.insert.assert_called()
            view.destroy()

    def test_send_callback(self):
        """Test that send callback can be set and called."""
        with patch("ai_ring_chat.view.views.tk.Tk"):
            view = TkinterView("127.0.0.1", 5000)
            callback_called = []

            def callback():
                callback_called.append(True)

            view.set_send_callback(callback)
            view._on_send()

            assert len(callback_called) == 1
            view.destroy()

    def test_user_click_callback(self):
        """Test that user click callback can be set."""
        with patch("ai_ring_chat.view.views.tk.Tk"):
            view = TkinterView("127.0.0.1", 5000)
            clicked_user = []

            def callback(user):
                clicked_user.append(user)

            view.set_user_click_callback(callback)
            view._user_listbox = MagicMock()
            view._user_listbox.curselection.return_value = [0]
            view._user_listbox.get.return_value = "127.0.0.1:5001"
            view._on_user_select(None)

            assert clicked_user == ["127.0.0.1:5001"]
            view.destroy()

    def test_close_callback(self):
        """Test that close callback can be set."""
        with patch("ai_ring_chat.view.views.tk.Tk"):
            view = TkinterView("127.0.0.1", 5000)
            callback_called = []

            def callback():
                callback_called.append(True)

            view.set_close_callback(callback)
            # The callback is stored, verify it exists
            assert view._close_callback is not None
            view.destroy()

    def test_prepend_user_to_input(self):
        """Test prepending user to input field."""
        with patch("ai_ring_chat.view.views.tk.Tk"):
            view = TkinterView("127.0.0.1", 5000)
            view._message_input = MagicMock()
            view._message_input.get.return_value = ""

            # No existing prefix
            view._prepend_user("127.0.0.1:5001")
            # Verify it was called with the prefixed message
            view._message_input.delete.assert_called()
            view._message_input.insert.assert_called()
            view.destroy()

    def test_prepend_user_replaces_existing(self):
        """Test that prepending user replaces existing prefix."""
        with patch("ai_ring_chat.view.views.tk.Tk"):
            view = TkinterView("127.0.0.1", 5000)
            view._message_input = MagicMock()
            view._message_input.get.return_value = "@127.0.0.1:5002 Hello world"

            # Existing prefix
            view._prepend_user("127.0.0.1:5001")
            view._message_input.delete.assert_called()
            view._message_input.insert.assert_called()
            view.destroy()

    def test_prepend_user_empty_input(self):
        """Test prepending user with empty input."""
        with patch("ai_ring_chat.view.views.tk.Tk"):
            view = TkinterView("127.0.0.1", 5000)
            view._message_input = MagicMock()
            view._message_input.get.return_value = ""

            # Empty input - should add @user with space
            view._prepend_user("127.0.0.1:5001")
            view._message_input.delete.assert_called()
            view._message_input.insert.assert_called()
            view.destroy()

    def test_prepend_user_with_text_no_prefix(self):
        """Test prepending user with text that has no existing prefix."""
        with patch("ai_ring_chat.view.views.tk.Tk"):
            view = TkinterView("127.0.0.1", 5000)
            view._message_input = MagicMock()
            # Regular text without @ prefix
            view._message_input.get.return_value = "Hello world"

            # No prefix, but has text - should add @user prefix
            view._prepend_user("127.0.0.1:5001")
            view._message_input.delete.assert_called()
            view._message_input.insert.assert_called()
            view.destroy()

    def test_view_show_method_concrete(self):
        """Test View.show method in MockView."""
        view = MockView()
        # Should not raise - just tests the method exists and is callable
        view.show()
        view.update_user_list(["user1"])
        view.append_message("test message")
        _ = view.get_message()
        view.clear_message()
        
        def send_cb():
            pass
        view.set_send_callback(send_cb)
        
        def user_cb(u):
            pass
        view.set_user_click_callback(user_cb)
        
        def close_cb():
            pass
        view.set_close_callback(close_cb)
        
        view.set_input_text("test")

    def test_prepend_user_own_address_not_shown(self):
        """Test that own address is not shown in user list."""
        with patch("ai_ring_chat.view.views.tk.Tk"):
            view = TkinterView("127.0.0.1", 5000)
            view._user_listbox = MagicMock()

            # Add self to list - should not appear
            view.update_user_list(["127.0.0.1:5000", "127.0.0.1:5001"])

            # Verify delete was called (clearing list)
            view._user_listbox.delete.assert_called_with(0, "end")
            # Verify only non-self address was inserted
            assert view._user_listbox.insert.call_count == 1
            view.destroy()

    def test_chat_log_limit(self):
        """Test that chat log is limited to 100 messages."""
        with patch("ai_ring_chat.view.views.tk.Tk"):
            view = TkinterView("127.0.0.1", 5000)
            view._chat_text = MagicMock()

            # Add more than 100 messages
            for i in range(150):
                view.append_message(f"Message {i}")

            # Check that log is limited to 100
            assert len(view._chat_log) == 100
            view.destroy()


class TestViewIntegration:
    """Integration tests for view components."""

    def test_view_with_mock_callbacks(self):
        """Test view with all callbacks set."""
        with patch("ai_ring_chat.view.views.tk.Tk"):
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
        with patch("ai_ring_chat.view.views.tk.Tk"):
            view = TkinterView("127.0.0.1", 5000)
            view._message_input = MagicMock()
            view._message_input.get.return_value = ""
            assert view.get_message() == ""
            view.destroy()

    def test_get_message_with_text(self):
        """Test get_message with text in input."""
        with patch("ai_ring_chat.view.views.tk.Tk"):
            view = TkinterView("127.0.0.1", 5000)
            view._message_input = MagicMock()
            view._message_input.get.return_value = "Test message"
            assert view.get_message() == "Test message"
            view.destroy()

    def test_on_close_with_callback(self):
        """Test _on_close calls callback when set."""
        with patch("ai_ring_chat.view.views.tk.Tk"):
            view = TkinterView("127.0.0.1", 5000)
            callback_called = []
            view.set_close_callback(lambda: callback_called.append(True))
            view._on_close()
            assert len(callback_called) == 1
            view.destroy()

    def test_on_close_without_callback(self):
        """Test _on_close handles no callback gracefully."""
        with patch("ai_ring_chat.view.views.tk.Tk"):
            view = TkinterView("127.0.0.1", 5000)
            # No callback set - should not raise
            view._on_close()
            view.destroy()

    def test_get_window_title(self):
        """Test get_window_title returns correct format."""
        with patch("ai_ring_chat.view.views.tk.Tk"):
            view = TkinterView("192.168.1.100", 5000)
            assert view.get_window_title() == "192.168.1.100:5000"
            view.destroy()

    def test_get_input_text_empty(self):
        """Test get_input_text when input is empty."""
        with patch("ai_ring_chat.view.views.tk.Tk"):
            view = TkinterView("127.0.0.1", 5000)
            view._message_input = MagicMock()
            view._message_input.get.return_value = ""
            assert view.get_input_text() == ""
            view.destroy()

    def test_send_callback_executes(self):
        """Test that send callback actually executes when triggered."""
        with patch("ai_ring_chat.view.views.tk.Tk"):
            view = TkinterView("127.0.0.1", 5000)
            called = []
            view.set_send_callback(lambda: called.append(True))
            view._on_send()
            assert len(called) == 1
            view.destroy()

    def test_user_click_callback_executes(self):
        """Test that user click callback executes when user selected."""
        with patch("ai_ring_chat.view.views.tk.Tk"):
            view = TkinterView("127.0.0.1", 5000)
            selected_user = []
            view.set_user_click_callback(lambda u: selected_user.append(u))
            view._user_listbox = MagicMock()
            view._user_listbox.curselection.return_value = [0]
            view._user_listbox.get.return_value = "127.0.0.1:5001"
            view._on_user_select(None)
            assert selected_user == ["127.0.0.1:5001"]
            view.destroy()
