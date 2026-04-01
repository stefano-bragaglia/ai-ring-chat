"""Tkinter implementation of the chat view."""

import tkinter as tk
from tkinter import ttk
import re

from ai_ring_chat.view import View

# Maximum number of messages to keep in chat log
MAX_CHAT_LOG = 100


class TkinterView(View):
    """Tkinter implementation of the chat view.

    Provides a GUI with:
    - User list (left side) - clickable to send private messages
    - Chat log (right side) - shows last 100 messages
    - Message input (bottom) - text field and send button
    """

    def __init__(self, address: str, port: int):
        """Initialize the Tkinter view.

        Args:
            address: The node's IP address
            port: The node's port number
        """
        self._address = address
        self._port = port
        self._send_callback = None
        self._user_click_callback = None
        self._close_callback = None
        self._chat_log: list[str] = []

        self._create_window()

    def _create_window(self) -> None:
        """Create the main window and widgets."""
        self._root = tk.Tk()
        self._root.title(self.get_window_title())
        self._root.protocol("WM_DELETE_WINDOW", self._on_close)

        # Main container with paned window
        self._paned = ttk.PanedWindow(self._root, orient=tk.HORIZONTAL)
        self._paned.pack(fill=tk.BOTH, expand=True)

        # Left frame - User list
        self._left_frame = ttk.Frame(self._paned, width=200)
        self._paned.add(self._left_frame, weight=1)

        ttk.Label(self._left_frame, text="Users", font=("Arial", 12, "bold")).pack(
            pady=5
        )

        self._user_listbox = tk.Listbox(self._left_frame)
        self._user_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self._user_listbox.bind("<<ListboxSelect>>", self._on_user_select)

        # Right frame - Chat log
        self._right_frame = ttk.Frame(self._paned)
        self._paned.add(self._right_frame, weight=3)

        ttk.Label(self._right_frame, text="Chat Log", font=("Arial", 12, "bold")).pack(
            pady=5
        )

        self._chat_text = tk.Text(self._right_frame, wrap=tk.WORD, state=tk.DISABLED)
        self._chat_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Bottom frame - Message input
        self._bottom_frame = ttk.Frame(self._root)
        self._bottom_frame.pack(fill=tk.X, padx=5, pady=5)

        self._message_input = ttk.Entry(self._bottom_frame)
        self._message_input.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self._message_input.bind("<Return>", lambda e: self._on_send())

        self._send_button = ttk.Button(
            self._bottom_frame, text="Send", command=self._on_send
        )
        self._send_button.pack(side=tk.RIGHT, padx=(5, 0))

    def show(self) -> None:
        """Display the view (start the GUI main loop)."""
        self._root.mainloop()

    def destroy(self) -> None:
        """Destroy the window."""
        if hasattr(self, "_root") and self._root:
            self._root.destroy()

    def update_user_list(self, users: list[str]) -> None:
        """Update the list of users shown in the view.

        Args:
            users: List of user addresses in format 'address:port'
        """
        # Filter out own address
        self_address = f"{self._address}:{self._port}"
        filtered_users = [u for u in users if u != self_address]

        self._user_listbox.delete(0, tk.END)
        for user in filtered_users:
            self._user_listbox.insert(tk.END, user)

    def append_message(self, message: str) -> None:
        """Append a message to the chat log.

        Args:
            message: The message to append
        """
        self._chat_log.append(message)

        # Trim log if exceeds max
        if len(self._chat_log) > MAX_CHAT_LOG:
            self._chat_log = self._chat_log[-MAX_CHAT_LOG:]

        # Update display
        self._chat_text.config(state=tk.NORMAL)
        self._chat_text.insert(tk.END, message + "\n")
        self._chat_text.see(tk.END)
        self._chat_text.config(state=tk.DISABLED)

    def get_message(self) -> str:
        """Get the current message from the input field.

        Returns:
            The message text
        """
        return self._message_input.get().strip()

    def clear_message(self) -> None:
        """Clear the message input field."""
        self._message_input.delete(0, tk.END)

    def set_send_callback(self, callback) -> None:
        """Set the callback for the send action."""
        self._send_callback = callback

    def set_user_click_callback(self, callback) -> None:
        """Set the callback for user list clicks."""
        self._user_click_callback = callback

    def set_close_callback(self, callback) -> None:
        """Set the callback for window close."""
        self._close_callback = callback

    def get_window_title(self) -> str:
        """Get the window title."""
        return f"{self._address}:{self._port}"

    def get_input_text(self) -> str:
        """Get the text from the message input field."""
        return self._message_input.get()

    def set_input_text(self, text: str) -> None:
        """Set the text in the message input field."""
        self._message_input.delete(0, tk.END)
        self._message_input.insert(0, text)

    def _on_send(self) -> None:
        """Handle send button click or Enter key."""
        if self._send_callback:
            self._send_callback()

    def _on_user_select(self, event) -> None:
        """Handle user selection in the list."""
        selection = self._user_listbox.curselection()
        if selection and self._user_click_callback:
            user = self._user_listbox.get(selection[0])
            self._user_click_callback(user)

    def _on_close(self) -> None:
        """Handle window close."""
        if self._close_callback:
            self._close_callback()
        self.destroy()

    def _prepend_user(self, user: str) -> None:
        """Prepend user address to the message input.

        Args:
            user: The user address in format 'address:port'
        """
        current_text = self.get_input_text()

        # Check if there's already a @address:port prefix
        pattern = r"^@\S+\s+"
        match = re.match(pattern, current_text)

        if match:
            # Replace existing prefix
            rest = current_text[match.end() :]
            self.set_input_text(f"@{user} {rest}")
        else:
            # Add new prefix
            if current_text:
                self.set_input_text(f"@{user} {current_text}")
            else:
                self.set_input_text(f"@{user} ")
