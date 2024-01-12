# Server word guessing game

This app consists of two parts, the server side and the client side.
In my implementation, the client side is configured to automatically connect to the server upon launch, since that is it's sole purpose.
When booted into the server, the client is instructed to enter a password, in my case: `please`. After that, the server responses are based only on client inputs. 

### Client input options
1. `-list` - Lists available opponents that are currently connected to the server
2. `-msg <target_id> <message>` - Sends a direct message to a client, can be used to give hints or just communicate
3. `-play <target_id>` - Initiates a game with the specified opponent
4. `exit` - disconnects client from the message/gives up the game
5. Any different input -> echoes back to the client, does nothing
