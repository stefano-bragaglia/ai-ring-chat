"""View abstract base class for the chat interface."""

from abc import ABC, abstractmethod


class View(ABC):
    """Abstract base class for the chat view.

    Defines the interface that all view implementations must follow.
    """

    @abstractmethod
    def show(self) -> None:
        """Display the view (start the GUI main loop)."""
        pass

    @abstractmethod
    def update_user_list(self, users: list[str]) -> None:
        """Update the list of users shown in the view.

        Args:
            users: List of user addresses in format 'address:port'
        """
        pass

    @abstractmethod
    def append_message(self, message: str) -> None:
        """Append a message to the chat log.

        Args:
            message: The message to append
        """
        pass

    @abstractmethod
    def get_message(self) -> str:
        """Get the current message from the input field.

        Returns:
            The message text
        """
        pass

    @abstractmethod
    def clear_message(self) -> None:
        """Clear the message input field."""
        pass

    @abstractmethod
    def set_send_callback(self, callback) -> None:
        """Set the callback for the send action.

        Args:
            callback: Function to call when send is triggered
        """
        pass

    @abstractmethod
    def set_user_click_callback(self, callback) -> None:
        """Set the callback for user list clicks.

        Args:
            callback: Function to call when a user is clicked (receives address:port)
        """
        pass

    @abstractmethod
    def set_close_callback(self, callback) -> None:
        """Set the callback for window close.

        Args:
            callback: Function to call when window is closed
        """
        pass
