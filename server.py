import socket
import threading
import os
from config import *


# The server object starts both types of sockets and manages traffic inbetween
class Server:
    def __init__(self):
        self._clients: dict[int, socket.socket] = {}
        self._client_id_counter: int = 0
        self._lock: threading.Lock = threading.Lock()

    # The word guessing game
    def word_game(
        self,
        client_a: socket.socket,
        client_b: socket.socket,
        word_to_guess: str,
    ) -> None:
        word: str = word_to_guess.lower()
        attempt_cnt: int = 0
        while True:
            # Receive guess from client_b
            guess = client_b.recv(MAX_MSG_LEN).decode("utf-8").lower()
            if guess == "-give_up":
                break
            if guess == word:
                # Client_b guessed the word correctly
                client_a.send(
                    "Congratulations! Your opponent guessed the word.".encode()
                )
                client_b.send(
                    f"Congratulations! You guessed the word '{word}' correctly.".encode()
                )
                return
            attempt_cnt += 1
            client_a.send(
                f"Attempt {attempt_cnt}: Your opponent guessed '{guess}'. Keep trying!".encode()
            )
            client_b.send(
                f"Attempt {attempt_cnt}: You guessed '{guess}'. Keep trying!".encode()
            )

        # Maximum attempts reached
        client_a.send(
            f"Game over! Your opponent couldn't guess the word '{word}'.".encode()
        )
        client_b.send(
            f"Game over! You couldn't guess the word '{word}'. The correct word was '{word}'.".encode()
        )
        return

    # Handles client connection and their requests and messages
    def handle_client(
        self,
        client_socket: socket.socket,
        address,
        client_id: int,
    ) -> None:
        print(f"Accepted connection from {address} with client ID {client_id}")

        # Send a welcome message to the client
        client_socket.send(f"Welcome, enter password".encode("utf-8"))

        password: bytes = client_socket.recv(MAX_MSG_LEN)
        if not password or password.decode().lower() != PASSWORD:
            client_socket.send("Wrong password.".encode())
            with self._lock:
                del self._clients[client_id]
            client_socket.close()
            return

        client_socket.send(f"Correct password, welcome, client {client_id}".encode())

        # Receive and handle client data
        while True:
            data: bytes = client_socket.recv(MAX_MSG_LEN)
            if not data:
                break

            decoded_data: str = data.decode("utf-8")
            print(f"Received data from Client {client_id}: {decoded_data}")

            # Message type cases
            # Send the specified message to the client with the specified id
            if decoded_data.startswith("-msg"):
                try:
                    _, target_client_id, message = decoded_data.split(" ", 2)
                    if not target_client_id or not message:
                        client_socket.send("Usage: -msg <client_id> <message>".encode())
                        continue
                    res : bool = self.send_direct_message(client_id, int(target_client_id), message)
                    if not res:
                        client_socket.send("Client ID doesn't exist.".encode())
                except Exception as e:
                    client_socket.send(f"{e}".encode())

            # Just send the client id list back to the client
            elif decoded_data.startswith("-list"):
                message: str = ""
                for client_id in self._clients:
                    message += f"{client_id}, "
                client_socket.send(message.encode())

            # Start a word guessing game with another client
            elif decoded_data.startswith("-play"):
                try:
                    _, target_client_id, word_to_guess = decoded_data.split(" ", 2)
                    if not target_client_id or not word_to_guess:
                        client_socket.send(
                            "Usage: -play <client_id> <word_to_guess>".encode()
                        )
                        continue
                    target_id: int = int(target_client_id)
                    if not target_id:
                        client_socket.send("Client ID needs to be a number.".encode())
                        continue
                    # Get target client socket
                    target_socket: socket.socket = self._clients.get(target_id)
                    if target_socket is None:
                        client_socket.send("Specified client doesn't exist".encode())
                        continue
                    # START GAME
                    with self._lock:
                        client_socket.send(
                            f"Starting word guessing game with Client {target_client_id}.".encode()
                        )
                        target_socket.send(
                            f"Starting word guessing game with Client {client_id}.".encode()
                        )
                        # target_socket.
                    # Start the word guessing game on a separate thread
                    game_thread = threading.Thread(
                        target=self.word_game,
                        args=(client_socket, target_socket, word_to_guess),
                    )
                    game_thread.start()
                    game_thread.join()
                except Exception as e:
                    client_socket.send(f"{e}".encode())

            else:
                # Echo message
                response = f"You said: {decoded_data}."
                client_socket.send(response.encode("utf-8"))

        # Close the client connection
        # Clean up socket
        print(f"Connection from {address} with client ID {client_id} closed.")
        with self._lock:
            del self._clients[client_id]
        client_socket.close()

    # Sends message to a client with specified ID
    def send_direct_message(
        self,
        sender_id: int,
        target_id: int,
        message,
    ) -> bool:
        with self._lock:
            target_socket = self._clients.get(target_id)
        if target_socket:
            formatted_message = f"Client {sender_id} says: {message}"
            target_socket.send(formatted_message.encode("utf-8"))
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
                self._clients[client_id] = client_socket

            client_thread = threading.Thread(
                target=self.handle_client,
                args=(client_socket, client_address, client_id),
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
                self._clients[client_id] = client_socket

            client_thread = threading.Thread(
                target=self.handle_client,
                args=(client_socket, SERVER_UNIX_PATH, client_id),
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
