# Only 1 client in queue
CLIENT_CNT : int = 5
MAX_MSG_LEN : int = 1024

# HTTP Response codes
OK : int = 100
ERR_UNAUTHORIZED : int = 401
ERR_NOT_FOUND : int = 404

# Password for accesing the server
PASSWORD : str = "please"
GIVE_UP : str = "exit"

# Server specifications
SERVER_TCP_PORT : int = 33333
SERVER_IP : str = "localhost"
SERVER_UNIX_PATH : str = "/tmp/unix_socket"
