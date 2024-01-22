# Server with a word guessing game
This is my implementation of the interview task. I have decided to use Python as it has the simplest standard socket and threading libraries. It consists of 2 parts, the server app and the client instance. I have kept it fairly simple, since Python is definitely not my main language as I have been learning it on the go. Since I'm fairly new to network programming, I have decided to stick to UTF-8 encoding. I know it was discouraged in the assignment, so I am aware of the shortcomings of this programme. Thank you for giving me the opportunity ot showcase my skills.

### Startup
1. Start the server app - `python3 server.py`
2. Connect the clients
    - For TCP `python3 tcp localhost unix_socket_path 33333`
    - For UNIX `python3 unix /tmp/unix_socket`

I've chosen the address, port and unix path so that it is easy to remember. It is possible to change this in the config file.

### Client connection
Once the client is connected, the client needs to input a password: `please`. This password can also be changed in the config file.

### Client input options
Once the client is connected and verified. They were assigned an ID number and can now send inputs.
While not being in th game, the client is able to send these types of messages:
    - `exit` - Disconnects client from the server
    - `-msg <client_id> <message>` This sends a direct private message to the client with the specified ID.
    - `-list` This lists all the connected active clients (their IDs).
    - `-play <client_id> <word_to_guess>` This initiates a game with the client with the spcified ID. The other client will have to guess the word that was specified.
    - Any other input will be echoed back to the client.

### While in game
Now that client A has initiated the game and client B was brought into the game as the guesser, client B can begin to guess the word just by typing an input.
The server then informs the client of their success/mistake.
Client A can at any time sed hints to client B by just typing anything into the input (client A has access to all attempted guesses).
Client B can surrender by typing `exit` the server will stop the game.
If client B guesses the right word, the server will alert both clients with the result.

### Shutting down the server
`Ctrl + C` will shut down the server with python KeyboardInterrupt