import json
import logging
import queue
import socket
import threading
import time

import xml.etree.ElementTree as Et
from jsonrpcclient import request, parse_json, Ok, Error
from .qrc_methods import ControlMethods, ComponentMethods, ChangeGroupMethods, MixerMethods, LoopPlayerMethods, \
    SnapshotMethods


class Core(object):
    """
    Class representing a QSC Core device

    """

    def __init__(self, ip, port=1710):
        super(Core, self).__init__()
        self.ip: str = ip
        self.port: int = port

        self.sock = None

        self.sock_thread = None
        self.keepalive_thread = None

        self.msg_queue = queue.Queue()
        self.response_queue = queue.Queue()
        self.keepalive_event = threading.Event()
        self.response_is_ready = threading.Event()
        self.stop_threads = threading.Event()

        self.noop_timer: int = 29
        self.noop_timer_lock = threading.Lock()

        self.Control = ControlMethods(self)
        self.Component = ComponentMethods(self)
        self.ChangeGroup = ChangeGroupMethods(self)
        self.Mixer = MixerMethods(self)
        self.LoopPlayer = LoopPlayerMethods(self)
        self.Snapshot = SnapshotMethods(self)
        self.controls = []

        logging.basicConfig(format="(%(levelname)s) %(asctime)s: %(message)s", level=logging.INFO, datefmt="%H:%M:%S")

    # ------------------------------------------------------- #
    # Thread function(s)                                      #
    # ------------------------------------------------------- #

    def sock_handler(self):
        data: bytes = b''
        while not self.stop_threads.is_set() or not self.msg_queue.empty():
            try:
                # receive data from the socket
                chunk = self.sock.recv(4096)
                data += chunk
                null_term_count = data.count(b'\00')
                if null_term_count > 0:
                    responses_and_any_overflow = data.split(b'\00')
                    for index, response in enumerate(responses_and_any_overflow):
                        # Last Element of list is possible overflow, write back to data var and break for loop
                        if index == null_term_count:
                            data = response
                            break
                        if response.count(b'EngineStatus') > 0:
                            # Log unsolicited EngineStatus messages
                            logging.info(response.decode('UTF8'))
                        else:
                            # Parse JSON and put parsed object into response_queue
                            self.response_queue.put(parse_json(response.decode('UTF8')))
                            self.response_is_ready.set()
            except BlockingIOError:
                # send data
                if not self.msg_queue.empty():
                    cmd = self.msg_queue.get()
                    if self._send_cmd(cmd):
                        with self.noop_timer_lock:
                            self.noop_timer = 29
                elif self.keepalive_event.is_set():
                    cmd: dict = {"jsonrpc": "2.0", "method": "NoOp", "params": {}}
                    self._send_cmd(cmd)
                    self.keepalive_event.clear()
                    with self.noop_timer_lock:
                        self.noop_timer = 29

    def keepalive(self):
        while not self.stop_threads.is_set() and self.sock_thread.is_alive():
            with self.noop_timer_lock:
                if not self.noop_timer:
                    self.keepalive_event.set()
                    self.noop_timer = 29
                    logging.info("NoOp - keep alive")
                else:
                    self.noop_timer -= 1
            time.sleep(1)

    # ------------------------------------------------------- #
    # Helper/private methods                                  #
    # ------------------------------------------------------- #

    def parse_response(self, cmd_id, parsed_json) -> dict:
        match parsed_json:
            case Ok(result, id):
                if id == cmd_id:
                    self.response_is_ready.clear()
                    return result
                else:
                    raise LookupError("Response has incorrect ID.")
            case Error(message):
                logging.error(message)
                return self._parse_error(message)

    @staticmethod
    def _parse_error(error_code: int) -> dict:
        match error_code:
            case -32700:
                return {"Error": "Parse error. Invalid JSON was received by the server.", "Code": error_code}
            case -32600:
                return {"Error": "Invalid request. The JSON sent is not a valid Request object.", "Code": error_code}
            case -32601:
                return {"Error": "Method not found.", "Code": error_code}
            case -32602:
                return {"Error": "Invalid params.", "Code": error_code}
            case -32603:
                return {"Error": "Server error.", "Code": error_code}
            case -32604:
                return {"Error": "Core is on Standby. This code is returned when a QRC command is received "
                                 "while the Core is not the active Core in a redundant Core configuration.",
                        "Code": error_code}
            case 2:
                return {"Error": "Invalid Page Request ID", "Code": error_code}
            case 3:
                return {"Error": "Bad Page Request - could not create the requested Page Request", "Code": error_code}
            case 4:
                return {"Error": "Missing file", "Code": error_code}
            case 5:
                return {"Error": "Change Groups exhausted", "Code": error_code}
            case 6:
                return {"Error": "Unknown change group", "Code": error_code}
            case 7:
                return {"Error": "Unknown component name", "Code": error_code}
            case 8:
                return {"Error": "Unknown control", "Code": error_code}
            case 9:
                return {"Error": "Illegal mixer channel index", "Code": error_code}
            case 10:
                return {"Error": "Logon required", "Code": error_code}

    @staticmethod
    def _build_cmd(method: str, params=None) -> dict:
        return request(method, params=params)

    def _send_cmd(self, cmd: dict):
        try:
            sent = self.sock.sendall(json.dumps(cmd).encode('UTF8') + b'\00')
            if sent is None:
                return True
        except Exception as e:
            raise e

    # ------------------------------------------------------- #
    # Public methods                                          #
    # ------------------------------------------------------- #
    def connect(self):
        logging.info("Connecting to Core...")
        if not self.sock_thread or not self.sock_thread.is_alive():
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock_thread = threading.Thread(target=self.sock_handler)
            self.keepalive_thread = threading.Thread(target=self.keepalive, daemon=True)
            self.sock.connect((self.ip, self.port))
            self.sock.setblocking(False)
            self.stop_threads.clear()
            self.response_is_ready.clear()
            self.keepalive_event.clear()
            self.sock_thread.start()
            self.keepalive_thread.start()
            logging.info("Connected")
        else:
            logging.error("Could not connect to core.")

    def logon(self, user, password):
        method_name: str = "Logon"
        params: dict = {"User": user, "Password": password}
        cmd = self._build_cmd(method_name, params)
        if self.sock_thread.is_alive():
            self.msg_queue.put(cmd)
            self.response_is_ready.wait()
            return self.parse_response(cmd["id"], self.response_queue.get())
        else:
            logging.error("Request could not be sent. There is no active connection to the core.")

    def close(self):
        self.stop_threads.set()
        self.sock_thread.join()
        self.sock.close()
        logging.info("Closed connection.")

    def no_op(self):
        if self.sock_thread.is_alive() and not self.keepalive_event.is_set():
            self.keepalive_event.set()
            with self.noop_timer_lock:
                self.noop_timer: int = 29
        else:
            logging.error("Request could not be sent. There is no active connection to the core.")

    def status_get(self) -> dict:
        method_name: str = "StatusGet"
        cmd: dict = self._build_cmd(method_name)
        if self.sock_thread.is_alive():
            self.msg_queue.put(cmd)
            self.response_is_ready.wait()
            return self.parse_response(cmd["id"], self.response_queue.get())
        else:
            logging.error("Request could not be sent. There is no active connection to the core.")
