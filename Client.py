import socket
import time
from datetime import datetime
from colorama import Fore, init, Back
import random
import threading

HOST = "127.0.0.1"
PORT = 5002
BUFFER_SIZE = 50000
global c
c = 0
init()

# set the available colors
colors = [Fore.BLUE, Fore.CYAN, Fore.GREEN, Fore.LIGHTBLACK_EX,
          Fore.LIGHTBLUE_EX, Fore.LIGHTCYAN_EX, Fore.LIGHTGREEN_EX,
          Fore.LIGHTMAGENTA_EX, Fore.LIGHTRED_EX, Fore.LIGHTWHITE_EX,
          Fore.LIGHTYELLOW_EX, Fore.MAGENTA, Fore.RED, Fore.WHITE, Fore.YELLOW
          ]

saprate = ":"


class Client:

    '''
    This is the constructor of the Client class. It can take the user name of not, its open a udp and tcp socket.
    It verifies if the user name is valid and if the user name is not valid it will ask for a new user name.
    It starts a threaf for listening to the server.
    '''

    def __init__(self, username=None):

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print(f"[*] Connecting to {HOST}:{PORT}...")
        self.sock.connect((HOST, PORT))
        self.tpcHost = self.sock.getsockname()[0]
        self.tpcPort = self.sock.getsockname()[1]
        self.client_color = random.choice(colors)
        if username:
            self.username = username
            self.sock.send(self.username.encode())
        else:
            self.username = input("Please enter your username: ")
            self.sock.send(self.username.encode())
            self.currAddr = None
            recv = self.sock.recv(BUFFER_SIZE).decode()
            while recv == "username already taken":
                print("username already taken")
                self.username = input("Please choose another username: ")
                self.sock.send(self.username.encode())
                recv = self.sock.recv(BUFFER_SIZE).decode()
        self.udpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.list_of_messages = []
        t = threading.Thread(target=self.listen_for_messages)
        t.daemon = True
        t.start()

    '''
    This function is used to send messages to the server by the client
    '''

    def send_message(self):
        while True:
            # input message we want to send to the server
                command = input("Enter command: ")
                if command == "<get_users>" or command == "<disconnect>" or command == "<get_files>" or command == "<proceed>" or \
                        command[:10] == "<download>" or command == "<get_messages>":

                    if command == "<get_messages>":
                        print(self.list_of_messages)

                    if command == "<disconnect>":
                        self.sock.send(command.encode())
                        time.sleep(0.2)
                        self.sock.close()
                        self.udpSocket.close()
                        exit()

                    if command == "<proceed>":
                        self.sock.send(command.encode())
                        print("[*] proceeding..")
                        self.udpSocket.sendto(command.encode(), self.currAddr)

                    if command[:10] == "<download>":
                        print("[*] Sending file...")
                        cmd = command + "~" + self.username
                        self.udpSocket.sendto(cmd.encode(), (HOST, PORT))

                    if command == "<get_users>" or command == "<get_files>":
                        self.sock.send(command.encode())

                else:
                    message = input("Enter message: ")
                    date_now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    message = f"{self.client_color}[{date_now}] {self.username}{saprate}{message}{Fore.RESET}{saprate}{command}"
                    self.sock.send(message.encode())

    '''
    This function is used to listen to the server and print the messages, above tcp messages. It also saves the messages.
    '''

    def listen_for_messages(self):
        while True:
            try:
                message = self.sock.recv(BUFFER_SIZE).decode()
                if message:
                    if message == "Sending file...":
                        self.get_file()
                    else:
                        self.list_of_messages.append(message)
                        print(message)
            except Exception as e:
                print(e)
                break
    '''
    This is the same send message function as above, but it is used to send by the arguments.
    '''
    def send_message_prop(self, cmd = None, msg = None):

        while True:
            # input message we want to send to the server
            if cmd:
                if cmd and not msg:
                    if cmd == "<get_users>" or cmd == "<disconnect>" or cmd == "<get_files>" or cmd == "<proceed>" or cmd[                                                                                                                      :10] == "<download>":
                        self.sock.send(cmd.encode())
                        if cmd == "<disconnect>":
                            self.sock.close()
                            self.udpSocket.close()
                            exit()

                        if cmd == "<proceed>":
                            print("[*] proceeding..")
                            self.udpSocket.sendto(cmd.encode(), self.currAddr)

                        if cmd[:10] == "<download>":
                            print("[*] Sending file...")
                            cmd = cmd + "~" + self.username
                            self.udpSocket.sendto(cmd.encode(), (HOST, PORT))
                    cmd = None
                    msg = None

                if cmd and msg:
                    command = cmd
                    message = msg
                    date_now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    message = f"{self.client_color}[{date_now}] {self.username}{saprate}{message}{Fore.RESET}{saprate}{command}"
                    self.sock.send(message.encode())
                    cmd = None
                    msg = None

    '''
    This function is used to get the file from the server, it sends ack for each packet.
    In the end it saves the file, and sends end to the server.
    '''
    def get_file(self):

        try:
            b = True
            while b:
                size, addr = self.udpSocket.recvfrom(BUFFER_SIZE)
                if len(size.decode().split("~")) == 1:
                    b = False
            self.currAddr = addr
            size = int(size)
            expectedData = []
            receivedData = []
            count = 0
            print("Receiving file...")
            print("len: ", size)
            for i in range(size):
                expectedData.append(i)
            while len(expectedData) > 0:
                data = self.udpSocket.recvfrom(50000)[0]
                if data:
                    data = str(data).split("~")
                    seq = data[0]
                    seq = seq[2:]
                    seq = int(seq)
                    info = data[2]
                    info = info[:-1]
                    if seq in expectedData:
                        receivedData.insert(seq, info)
                        expectedData.remove(seq)
                        self.udpSocket.sendto(("ACK" + str(seq)).encode(), addr)
                        print("ACK" + str(seq))
                        count += 1
                        if seq == (size / 2):
                            print("50%, waiting for proceed...")
                            b = True
                            while b:
                                cmd = self.sock.recv(1024).decode()
                                if cmd == "<proceeding>":
                                    print("[*] Proceeding...")
                                    b = False
                                else:
                                    if seq in expectedData:
                                        print("seq #", seq)
                                        receivedData.insert(seq, info)
                                        expectedData.remove(seq)
                                        self.udpSocket.sendto(("ACK" + str(seq)).encode(), addr)
                                        print("[*] Sending ACK...", seq)
                    else:
                        self.udpSocket.sendto(("NACK" + str(expectedData[0])).encode(), addr)
                        self.udpSocket.sendto(("NACK" + str(expectedData[0])).encode(), addr)
            self.udpSocket.sendto(("end").encode(), addr)
            print("[*] File received")
            self.list_of_messages.append("end_of_file")
            global c
            file = open("received_file" + str(c) + ".txt", "w")
            for d in receivedData:
                file.write(d)
            file.close()
            c+=1
        except Exception as e:
            print(e)

    def calculate_checksum(self, data):
        checksum = 0
        for byte in data:
            checksum += byte
        checksum = checksum % 256
        return checksum


if __name__ == '__main__':
    c1 = Client()
    c1.send_message()
