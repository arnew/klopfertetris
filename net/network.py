# net/network.py
import socket, threading, time, json

BCAST_PORT_DEFAULT = 50000
BCAST_ADDR_DEFAULT = "<broadcast>"

class NetworkNode:
    def __init__(self, player_id, player_name, port=BCAST_PORT_DEFAULT, bcast_addr=BCAST_ADDR_DEFAULT):
        self.player_id = player_id
        self.player_name = player_name
        self.port = port
        self.bcast_addr = bcast_addr
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.sock.bind(("", port))
        self.running = False
        self.peers = {}  # id -> (ip, last_seen, name)
        self.on_garbage = None  # callback (from_id, to_id, lines)

    def start(self):
        self.running = True
        self._tx_hello()
        t = threading.Thread(target=self._rx_loop, daemon=True)
        t.start()
        t2 = threading.Thread(target=self._hello_loop, daemon=True)
        t2.start()

    def stop(self):
        self.running = False

    def _hello_loop(self):
        while self.running:
            self._tx_hello()
            time.sleep(5)

    def _tx_hello(self):
        msg = f"HELLO {self.player_id} {self.player_name}"
        try:
            self.sock.sendto(msg.encode("utf-8"), (self.bcast_addr, self.port))
        except Exception:
            pass

    def _rx_loop(self):
        while self.running:
            try:
                data, addr = self.sock.recvfrom(4096)
                s = data.decode("utf-8", "replace").strip()
                if s.startswith("HELLO"):
                    parts = s.split(" ",2)
                    if len(parts) >=3:
                        pid = parts[1]; name = parts[2]
                        self.peers[pid] = (addr[0], time.time(), name)
                elif s.startswith("GARBAGE"):
                    parts = s.split()
                    # GARBAGE from to lines
                    # example: GARBAGE P1 P2 3
                    if len(parts) >=4:
                        _, from_id, to_id, lines = parts[:4]
                        lines = int(lines)
                        if self.on_garbage:
                            self.on_garbage(from_id, to_id, lines)
                # ignore other messages
            except Exception:
                time.sleep(0.01)

    def send_garbage(self, to_id, lines):
        msg = f"GARBAGE {self.player_id} {to_id} {int(lines)}"
        try:
            self.sock.sendto(msg.encode("utf-8"), (self.bcast_addr, self.port))
        except Exception:
            pass
