from io import IOBase


class File:
    def __init__(self, file: IOBase, filename: str) -> None:
        """A representation of a file and filename.

        :param file: The file object.
        :type file: IOBase
        :param filename: The filename.
        :type filename: str
        """

        self.file = file
        self.filename = filename

    def reset(self) -> None:
        """Reset the file."""

        self.file.seek(0)
