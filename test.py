import threading

def inner_thread():
    while True:
        msg : str = input("")
        if msg.lower() == "exit":
            break
        print(f"inner: {msg}")

def main_thread():
    while True:
        msg : str = input("")
        if msg.lower() == "exit":
            break
        if msg.lower() == "inner":
            inner = threading.Thread(target=inner_thread)
            inner.start()
            inner.join()
        print(f"main: {msg}")

if __name__ == "__main__":
    main = threading.Thread(target=main_thread)
    main.start()
    main.join()