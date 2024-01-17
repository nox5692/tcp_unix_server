# Server word guessing game

This app consists of two parts, the server side and the client side.
In my implementation, the client side is configured to automatically connect to the server upon launch, since that is it's sole purpose.
When booted into the server, the client is instructed to enter a password, in my case: `please`. After that, the server responses are based only on client inputs. 

### Startup
1. Start the server app - `python3 server.py`
2. Connect the clients
    - For TCP `python3 tcp localhost unix_socket_path 33333`
    - For UNIX `python3 unix /tmp/unix_socket`

### Client input options
1. `-list` - Lists available opponents that are currently connected to the server
2. `-play <target_id>` - Initiates a game with the specified opponent
3. `-accept` - Client B enters this when clients A starts game
4. `-msg <target_id> <message>` - Sends a direct message to a client, can be used to give hints or just communicate
5. `exit` - disconnects client from the message/gives up the game
6. Any different input -> echoes back to the client, does nothing
