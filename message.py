class Message:
    def __init__(self, content: bytes, code: int = 100):
        self._content: bytes = content
        self._code: int = code
