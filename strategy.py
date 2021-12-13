from multiprocessing import Process, Pipe
from motors import motors

# Connection Globals
vision_conn = 0
motors_conn = 0
motors_p = 0


def initialize_motors_process():
    global motors_conn, motors_p
    motors_conn, child_conn = Pipe()
    motors_p = Process(target=motors, args=(child_conn,))
    motors_p.start()
    # Wait for motors process to initialize
    motors_init = motors_conn.recv()
    if not (motors_init[0] == 1 and motors_init[1]):
        print("Failed to initialize motors.")
        terminate_strategy()


def terminate_strategy():
    print("Strategy terminating.")
    # If motors initialized
    if motors_p != 0:
        if motors_p.is_alive():
            motors_p.terminate()
        motors_p.close()
    # If motors connection initialized
    if motors_conn != 0:
        motors_conn.close()
    exit()


def strategy(conn):
    global vision_conn
    vision_conn = conn

    print("Initializing motors.")
    initialize_motors_process()
    print("Motors initialized.")

    # Inform vision that process initialized successfully
    vision_conn.send([1, True])

    while(True):
        msg = vision_conn.recv()
        # If terminate request
        if msg[0] == 0:
            terminate_strategy()
        motors_conn.send(msg)

