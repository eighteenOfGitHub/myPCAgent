# app/logging/session_context_filter.py
"""Provides utilities for managing and injecting Session IDs into log records.

This module uses thread-local storage to hold the Session ID, making it suitable
for multi-threaded applications where each thread might represent a distinct
session or task flow.
It also defines a logging Filter to inject the Session ID into LogRecord objects.
"""

import threading
import logging

# --- 1. Thread-Local Storage for Session ID ---

# Create a thread-local storage object.
# Each thread will have its own independent `session_id` attribute within
# `_local_state`.
_local_state = threading.local()

# Define a constant for when no session ID is set.
_NO_SESSION_ID = 'NoSession'


def set_session_id(sid: str) -> None:
    """
    Sets the Session ID for the current thread.

    Args:
        sid (str): The Session ID to associate with the current thread.
                   If None or empty, it effectively clears the session ID.
    """
    if sid:  # Only set if a valid ID is provided
        _local_state.session_id = sid
    else:
        # If None or empty string is passed, treat it as clearing
        clear_session_id()


def get_session_id() -> str:
    """
    Gets the Session ID for the current thread.

    Returns:
        str: The Session ID associated with the current thread.
             Returns 'NoSession' if no ID has been set for this thread.
    """
    # Use getattr with a default value to safely retrieve the attribute.
    # If `session_id` hasn't been set on `_local_state` for this thread,
    # it returns the default `_NO_SESSION_ID`.
    return getattr(_local_state, 'session_id', _NO_SESSION_ID)


def clear_session_id() -> None:
    """
    Clears the Session ID for the current thread.
    This removes the `session_id` attribute from the thread's local storage.
    """
    # Check if the attribute exists before trying to delete it
    # to avoid potential AttributeError (though `delattr` usually handles it).
    if hasattr(_local_state, 'session_id'):
        delattr(_local_state, 'session_id')
    # If it doesn't exist, clearing is effectively a no-op.


# --- 2. Custom Logging Filter to Inject Session ID ---

class SessionIdInjectingFilter(logging.Filter):
    """
    A logging filter that injects the current thread's Session ID
    into the LogRecord's attributes.

    This allows the logging formatter configuration to reference
    the Session ID using %(session_id)s.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        """
        Applies the filter to a LogRecord.

        Adds a 'session_id' attribute to the LogRecord based on the
        current thread's session ID obtained via get_session_id().

        Args:
            record (logging.LogRecord): The log record to be filtered/modified.

        Returns:
            bool: Always True, indicating the record should be processed
                  (the filter does not discard records).
        """
        # Get the session ID for the current thread
        # This call is efficient because `get_session_id` uses thread-local
        # storage.
        current_session_id = get_session_id()

        # Inject the session ID directly into the LogRecord object as a new attribute.
        # The name 'session_id' should match what is used in the logging format
        # string.
        record.session_id = current_session_id

        # Return True to indicate that the record passes the filter and should
        # be logged.
        return True

# --- 3. (Optional) Convenience Function for Logger Setup ---
# This part is optional and depends on how you manage your loggers.
# If you want to automatically attach this filter to specific or all loggers,
# you could add a helper function here or in core/config.py during logging setup.
# For now, we'll assume manual attachment or configuration via
# logging_config.yaml.

# Example of how you *might* use it programmatically (usually done in config/setup):
# def add_session_filter_to_logger(logger_name: Optional[str] = None):
#     """Adds the SessionIdInjectingFilter to a specified logger (or root logger)."""
#     target_logger = logging.getLogger(logger_name)
#     # Avoid adding the same filter multiple times
#     if not any(isinstance(f, SessionIdInjectingFilter) for f in target_logger.filters):
#         target_logger.addFilter(SessionIdInjectingFilter())
