import sys
import traceback


class ImouException(Exception):
    def __init__(self, message: str = "") -> None:
        """Initialize."""
        self.message = message
        super().__init__(self.message)

    def to_string(self) -> str:
        """Return the exception as a string."""
        return f"{self.__class__.__name__}: {self.message}\n" + self.traceback()

    def traceback(self) -> str:
        """Return the traceback as a string."""
        etype, value, trace = sys.exc_info()
        return "".join(traceback.format_exception(etype, value, trace, None))

    def get_title(self) -> str:
        """Return the title of the exception which will be then translated."""
        return "generic_error"


class ConnectFailedException(ImouException):
    """connectFailedException. """

    def get_title(self) -> str:
        """Return the title of the exception which will be then translated."""
        return "connect_failed"


class RequestFailedException(ImouException):
    """requestFailedException """

    def get_title(self) -> str:
        """Return the title of the exception which will be then translated."""
        return "request_failed"


class InvalidAppIdOrSecretException(ImouException):
    """invalidAppIdOrSecretException """

    def get_title(self) -> str:
        """Return the title of the exception which will be then translated."""
        return "appIdOrSecret_invalid"
