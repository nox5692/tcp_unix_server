import socket
import threading
import sys
from enum import Enum
from config import *



def print_usage() -> None:
    print('Usage: ["tcp", "unix"] [address, socket_path] [tcp_port (only for tcp)]')


# Represents the possible socket types the client can choose
class SocketType(Enum):
    TCP = "tcp"
    UNIX = "unix"


# The Client is an encapsulation of the process of connection to a socket as a client
class Client:
    # Client class constructor
    # Prepares the instance by settings its socket type and passing through server info
    def __init__(self, server_info: list[str]):
        self._type: str = server_info[0].lower()
        self._server_info: list[str] = server_info[1:]
        self._socket: socket.socket = None  # Leave client socket unitialized until the start instruction is called
        self._lock: threading.Lock = threading.Lock()
        self._connected: bool = False

    # Connect client to a server of his choosing
    # Options are the SocketType enumerations
    # Returns true is connected sucesfully, flase if not
    def connect(self) -> bool:
        try:
            if self._type == SocketType.TCP.value:
                self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self._socket.connect((self._server_info[0], int(self._server_info[1])))
                self._connected = True
                return True
            elif self._type == SocketType.UNIX.value:
                self._socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                self._socket.connect(self._server_info[0])
                self._connected = True
                return True
            else:
                print("Invalid socket type.")
        except Exception as e:
            print(e)
            self._connected = False
            return False
        finally:
            if not self._connected:
                print("Connection failed.")
                self._socket.close()

    # Sends message through current socket
    def send_message(self, message: str) -> None:
        try:
            with self._lock:
                self._socket.send(message.encode("utf-8"))
        except BrokenPipeError:
            print("Server disconnected you.")
            self._socket.close()

    # Infinitely watches messages coming from the server
    def recv_message(self, stop_event: threading.Event) -> None:
        while not stop_event.is_set():
            try:
                server_response = self._socket.recv(MAX_MSG_LEN)
                if not server_response:
                    break
                print("Server:", server_response.decode('utf-8'))
            except socket.error as e:
                print("Error receiving message:", e)
                break
        self._connected = False


    # Starts communicating with the server that the client is currently connected to
    def communicate(self) -> None:
        if not self._connected:
            return
        stop_event = threading.Event()
        recv_thread = threading.Thread(target=self.recv_message, args=(stop_event,))
        recv_thread.start()

        try:
            while True:
                new_message: str = input("")
                self.send_message(new_message)
                if new_message.lower() == "exit":
                    break
                if not self._connected:
                    break

        except KeyboardInterrupt:
            print("KeyboardInterrupt: Exiting...")

        finally:
            stop_event.set()
            recv_thread.join()
            with self._lock: # Cleanup
                if self._socket.fileno() != -1:
                    self._socket.shutdown(socket.SHUT_RDWR)  # Shutdown both send and receive operations
                    self._socket.close()
                    print("Cleanup complete.")
                else:
                    print("Connection already closed.")


if __name__ == "__main__":
    arguments: list[str] = sys.argv[1:]
    if len(arguments) < 2 and arguments[0] == SocketType.UNIX.value:
        print_usage()
        exit(1)
    if len(arguments) < 3 and arguments[0] == SocketType.TCP.value:
        print_usage()
        exit(1)

    client: Client = Client(arguments)
    res: bool = client.connect()
    if not res:
        exit(1)
    client.communicate()
