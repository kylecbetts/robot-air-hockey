from multiprocessing import Process, Pipe

# Connection Globals
strategy_conn = 0


def terminate_motors():
    print("Motors terminating.")
    exit()


def motors(conn):
    global strategy_conn
    strategy_conn = conn

    # Inform strategy that process initialized successfully
    strategy_conn.send([1, True])

    while(True):
        msg = strategy_conn.recv()
        print(msg)
