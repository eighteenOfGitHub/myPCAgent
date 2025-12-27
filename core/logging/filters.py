# app/logging/session_context_filter.py

import threading
import logging

_local_state = threading.local()
_NO_SESSION_ID = 'NoSession'


def set_session_id(sid: str) -> None:
    if sid:
        _local_state.session_id = sid
    else:
        clear_session_id()


def get_session_id() -> str:
    return getattr(_local_state, 'session_id', _NO_SESSION_ID)


def clear_session_id() -> None:
    if hasattr(_local_state, 'session_id'):
        delattr(_local_state, 'session_id')


class SessionIdInjectingFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.session_id = get_session_id()
        return True