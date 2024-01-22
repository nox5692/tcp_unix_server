import socket
import threading
import os
from config import *


class ConnectedClient:
    def __init__(self, client_id: int, client_socket: socket.socket):
        self._client_id: int = client_id
        self._client_socket: socket.socket = client_socket
        self._is_in_game: bool = False
        self._in_game_with: int = None
        self._is_guessing: bool = None  # If true, is client B, if false, is client A
        self._word_to_guess: str = None


# The server object starts both types of sockets and manages traffic in between
class Server:
    def __init__(self):
        self._clients: dict[int, ConnectedClient] = {}
        self._client_id_counter: int = 1  # First client will have the ID of 1
        self._lock: threading.Lock = threading.Lock()


    # Handles client connection and their requests and messages
    def handle_client(
        self,
        connected_client: ConnectedClient,
    ) -> None:
        print(
            f"Accepted connection from {connected_client._client_socket.getpeername()} with client ID {connected_client._client_id}"
        )

        # Send a welcome message to the client
        connected_client._client_socket.send(f"Welcome, enter password".encode("utf-8"))

        # Reuest client password 
        password: bytes = connected_client._client_socket.recv(MAX_MSG_LEN)
        if not password or password.decode().lower() != PASSWORD:
            connected_client._client_socket.send("Wrong password.".encode())
            with self._lock:
                del self._clients[connected_client._client_id]
            connected_client._client_socket.close()
            return
        connected_client._client_socket.send(
            f"Correct password, welcome, client {connected_client._client_id}".encode()
        )

        # Receive and handle client data
        while True:
            # Get input from client
            data: bytes = connected_client._client_socket.recv(MAX_MSG_LEN)
            if not data:
                break
            decoded_data: str = data.decode("utf-8")
            print(
                f"Received data from Client {connected_client._client_id}: {decoded_data}"
            )

            # If game is played
            if self._clients.get(connected_client._client_id)._is_in_game:
                # If the guesser is playing
                if self._clients.get(connected_client._client_id)._is_guessing:
                    if (
                        decoded_data.lower()
                        == self._clients.get(connected_client._client_id)._word_to_guess
                    ):
                        connected_client._client_socket.send("You have won!".encode())
                        self._clients.get(
                            self._clients.get(connected_client._client_id)._in_game_with
                        )._client_socket.send(
                            f"Opponent has guessed correctly: {decoded_data}".encode()
                        )
                        self._clients.get(
                            self._clients.get(connected_client._client_id)._in_game_with
                        )._is_in_game = False
                        self._clients.get(
                            self._clients.get(connected_client._client_id)._in_game_with
                        )._in_game_with = None
                        self._clients.get(
                            self._clients.get(connected_client._client_id)._in_game_with
                        )._is_guessing = None
                        self._clients.get(
                            self._clients.get(connected_client._client_id)._in_game_with
                        )._word_to_guess = None
                        self._clients.get(
                            connected_client._client_id
                        )._is_in_game = False
                        self._clients.get(
                            connected_client._client_id
                        )._in_game_with = None
                        self._clients.get(
                            connected_client._client_id
                        )._is_guessing = None
                        self._clients.get(
                            connected_client._client_id
                        )._word_to_guess = None
                        continue
                    else:
                        connected_client._client_socket.send("Wrong.".encode())
                        self._clients.get(
                            self._clients.get(connected_client._client_id)._in_game_with
                        )._client_socket.send(
                            f"Opponent has guessed incorrectly: {decoded_data}".encode()
                        )
                        continue
                # If the instigator is playing
                else:
                    # We will send a hint to the guesser if needed
                    self._clients.get(
                        connected_client._in_game_with
                    )._client_socket.send(f"Hint: {decoded_data}".encode())
                    continue
            # If game is not played
            else:
                # Send the specified message to the client with the specified id
                if decoded_data.startswith("-msg"):
                    try:
                        _, target_client_id, message = decoded_data.split(" ", 2)
                        if not target_client_id or not message:
                            connected_client._client_socket.send(
                                "Usage: -msg <client_id> <message>".encode()
                            )
                            continue
                        res: bool = self.send_direct_message(
                            connected_client._client_id, int(target_client_id), message
                        )
                        if not res:
                            connected_client._client_socket.send(
                                "Client ID doesn't exist.".encode()
                            )
                    except Exception as e:
                        connected_client._client_socket.send(f"{e}".encode())

                # Just send the client id list back to the client
                elif decoded_data.startswith("-list"):
                    message: str = ""
                    with self._lock:
                        for client_id in self._clients:
                            message += f"{client_id}, "
                    connected_client._client_socket.send(message.encode())

                # Start a word guessing game with another client
                elif decoded_data.startswith("-play"):
                    try:
                        _, target_client_id, word_to_guess = decoded_data.split(" ", 2)
                        if not target_client_id or not word_to_guess:
                            connected_client._client_socket.send(
                                "Usage: -play <client_id> <word_to_guess>".encode()
                            )
                            continue
                        target_id: int = int(target_client_id)
                        if not target_id:
                            connected_client._client_socket.send(
                                "Client ID needs to be a number.".encode()
                            )
                            continue
                        # Get target client socket
                        target_client = None
                        with self._lock:
                            target_client = self._clients.get(target_id)
                        if target_client is None:
                            connected_client._client_socket.send(
                                "Specified client doesn't exist.".encode()
                            )
                            continue
                        if target_client._is_in_game:
                            connected_client._client_socket.send(
                                "Specified client is already in a game.".encode()
                            )
                            continue
                        # START GAME
                        target_client._is_in_game = True
                        target_client._in_game_with = connected_client._client_id
                        target_client._word_to_guess = word_to_guess
                        target_client._is_guessing = True
                        self._clients.get(
                            connected_client._client_id
                        )._is_in_game = True
                        self._clients.get(
                            connected_client._client_id
                        )._in_game_with = target_client._client_id
                        self._clients.get(
                            connected_client._client_id
                        )._word_to_guess = word_to_guess
                        self._clients.get(
                            connected_client._client_id
                        )._is_guessing = False

                        with self._lock:
                            connected_client._client_socket.send(
                                f"Starting word guessing game with Client {target_client_id}.".encode()
                            )
                            target_client._client_socket.send(
                                f"Starting word guessing game with Client {connected_client._client_id}.".encode()
                            )
                    except Exception as e:
                        connected_client._client_socket.send(f"{e}".encode())

                else:
                    # Echo message
                    response = f"You said: {decoded_data}."
                    connected_client._client_socket.send(response.encode("utf-8"))

        # Close the client connection
        # Clean up socket
        print(
            f"Connection from {connected_client._client_socket.getpeername()} with client ID {connected_client._client_id} closed."
        )
        with self._lock:
            del self._clients[connected_client._client_id]
        connected_client._client_socket.close()

    # Sends message to a client with specified ID
    def send_direct_message(
        self,
        sender_id: int,
        target_id: int,
        message,
    ) -> bool:
        with self._lock:
            target_client = self._clients.get(target_id)
        if target_client:
            formatted_message = f"Client {sender_id} says: {message}"
            target_client._client_socket.send(formatted_message.encode("utf-8"))
            return True
        else:
            print(f"Error: Client {target_id} not found.")
            return False

    # Creates and manages the tcp socket traffic
    # In my implementation, is run in a separate thread
    def start_tcp_server(self) -> None:
        tcp_server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp_server_socket.bind((SERVER_IP, SERVER_TCP_PORT))
        tcp_server_socket.listen()

        print(f"TCP Server listening on port {SERVER_TCP_PORT}")

        while True:
            client_socket, client_address = tcp_server_socket.accept()

            with self._lock:
                client_id = self._client_id_counter
                self._client_id_counter += 1
                connected_client = ConnectedClient(client_id, client_socket)
                self._clients[client_id] = connected_client

            client_thread = threading.Thread(
                target=self.handle_client,
                args=(connected_client,),
            )
            client_thread.start()

    # Creates and manage the unix socket traffic
    # Starts in the main thread
    def start_unix_server(self) -> None:
        unix_server_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

        # Remove the existing socket file if it exists
        if os.path.exists(SERVER_UNIX_PATH):
            os.remove(SERVER_UNIX_PATH)

        unix_server_socket.bind(SERVER_UNIX_PATH)
        unix_server_socket.listen()

        print(f"Unix Server listening on path {SERVER_UNIX_PATH}")

        while True:
            client_socket, _ = unix_server_socket.accept()

            with self._lock:
                client_id = self._client_id_counter
                self._client_id_counter += 1
                connected_client: ConnectedClient = ConnectedClient(
                    client_id, client_socket
                )
                self._clients[client_id] = connected_client

            client_thread = threading.Thread(
                target=self.handle_client,
                args=(connected_client,),
            )
            client_thread.start()

    # Starts both sockets on separate threads
    def start(self) -> None:
        # Start TCP server in a separate thread
        tcp_server_thread = threading.Thread(target=self.start_tcp_server)
        tcp_server_thread.start()

        # Start Unix server in the main thread
        self.start_unix_server()


if __name__ == "__main__":
    server = Server()
    server.start()
