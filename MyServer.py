import random
import threading
import socket
import time
from os import listdir
from os.path import isfile, join

HOST = "127.0.0.1"
PORT = 5002
BUFFER_SIZE = 50000

class MyServer:

    portCounter = 6000

    def __init__(self, host, port):

        self.host = host
        self.port = port
        self.dict_of_sockets = {}
        self.client_count = 0
        self.list_of_files = []
        self.dict_of_users = {}
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        self.udpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udpSocket.bind((self.host, self.port))

    '''
    This function is used to get the user and save all the relevant information and starts a separate thread for tcp 
    connection and udp connection. it also checks if the username is already taken.
    '''

    def accept_clients(self):
        print("Waiting for clients...")
        while True:
            client_socket, address = self.server_socket.accept()
            data = client_socket.recv(1024)
            while data.decode() in self.dict_of_sockets.keys():
                client_socket.send("username already taken".encode())
                data = client_socket.recv(1024)
            client_socket.send("username accepted".encode())
            self.dict_of_sockets[data.decode()] = client_socket
            self.dict_of_users[data.decode()] = address
            self.client_count += 1
            if self.client_count > 5:
                print("Max number of clients reached")
                client_socket.send("Max number of clients reached".encode())
                client_socket.close()
            else:
                print("Client connected: {}".format(address))
                client_socket.send("<connected>".encode())
                client_thread = threading.Thread(target=self.handle_client, args=(address, data.decode()))
                client_thread.daemon = True
                client_thread.start()
                udp_thread = threading.Thread(target=self.handle_udp, args=(client_socket, data.decode()))
                udp_thread.daemon = True
                udp_thread.start()

    '''
    This function is used to handle the udp connection.
    '''

    def handle_udp(self, client_socket, username):
        while True:
            try:
                d, addr = self.udpSocket.recvfrom(1024)
                d = d.decode()
                if d == "<proceed>":
                    d = None
                else:
                    d = d.split("~")
                    if len(d) == 2:
                        username = d[1]
                    d = d[0]
                    if d[:10] == "<download>":
                        tmpUDPSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                        rnd = random.randint(50000, 60000)
                        tmpUDPSock.bind((self.host, rnd))
                        self.send_file(client_socket, addr, d[11:-1], username, tmpUDPSock)
            except:
                pass
            time.sleep(1)

    '''
    This function is used to handle the client requests, this function is called in a thread
    '''

    def handle_client(self, address, user):
        while True:
            try:
                data = self.dict_of_sockets[user].recv(1024)
                if data:
                    if data.decode() == "<get_users>":
                        self.dict_of_sockets[user].send(str(self.dict_of_users).encode())
                        data = None
                    if data:
                        if data.decode() == "<disconnect>":
                            self.dict_of_sockets[user].send("<disconnected>".encode())
                            print("Client disconnected: {}".format(address))
                            self.dict_of_sockets[user].close()
                            del self.dict_of_sockets[user]
                            self.client_count -= 1
                            data = None
                            break
                    if data:
                        if data.decode() == "<get_files>":
                            self.dict_of_sockets[user].send(str(self.get_list_of_files()).encode())
                            data = None
                    if data:
                        if data.decode()[:10] == "<download>" or data.decode() == "<proceed>":
                            data = None

                if data:
                    print("data", data.decode())
                    dest = str(data.decode()).split(":")[4]
                    data = str(data.decode()).split(":")[0] + ":" + str(data.decode()).split(":")[1] + ":" + \
                           str(data.decode()).split(":")[2] + ":" + str(data.decode()).split(":")[3]
                    if dest == "all":
                        for key in self.dict_of_sockets.keys():
                            if key != user:
                                self.dict_of_sockets[key].send(data.encode())
                    else:
                        for client in self.dict_of_sockets.keys():
                            if client == dest:
                                self.dict_of_sockets[client].send(data.encode())

            except Exception as e:
                print("Client disconnected: {}".format(address))
                self.dict_of_sockets[user].close()
                del self.dict_of_sockets[user]
                self.client_count -= 1
                break

    '''
    This function is used to send a file to the client
    '''

    def send_file(self, socket, addr, filename, user, tmpUDPSock):
        flg2 = True
        self.dict_of_sockets[user].send("Sending file...".encode())
        window_size = 4
        data, size = self.split(filename, BUFFER_SIZE - 100)
        count = 0
        tmpUDPSock.sendto(str(size).encode(), addr)
        expectedData = []
        for i in range(size):
            expectedData.append(i)
        tmpUDPSock.settimeout(0.2)
        try:
            while count < size and count < window_size:
                tmpUDPSock.sendto(data[count], addr)
                print("sent packet #", count)
                count += 1
            flag = True

            while len(expectedData) > 0 and flag:
                ack = tmpUDPSock.recvfrom(32)[0].decode()
                if ack:
                    if ack == "end":
                        flag = False
                if ack:
                    print(ack)
                    if ack[:3] == "ACK":
                        if int(ack[3:]) == size / 2:
                            print("half done, wait for proceeding")
                            b = True
                            while b:
                                try:
                                    proc = tmpUDPSock.recvfrom(32)[0].decode()
                                    print(proc, "wait for proceeding")
                                    if proc == "<proceed>":
                                        print("proceeding")
                                        self.dict_of_sockets[user].send("<proceeding>".encode())
                                        for i in range(window_size):
                                            tmpUDPSock.sendto(data[count], addr)
                                            count += 1
                                            print("sent packet #", count)
                                        b = False
                                except Exception as e:
                                    pass
                        if int(ack[3:] == str(expectedData[0])):
                            expectedData.remove(int(ack[3:]))
                            if count < size:
                                tmpUDPSock.sendto(data[count], addr)
                                count += 1
                                print("sent packet #", count)
                        else:
                            if len(expectedData) > 1:
                                tmpUDPSock.sendto(data[expectedData[0]], addr)
                                tmpUDPSock.sendto(data[expectedData[1]], addr)
                                expectedData.remove(int(ack[3:]))
                                print("Sepical sent #", int(expectedData[0]))
                            if flg2:
                                flg2 = False
                    if ack[:4] == "NACK":
                        tmpUDPSock.sendto(data[int(ack[4:])], addr)
            print(filename + " sent")
        except Exception as e:
            print("timeout")
            time.sleep(0.1)
            tmpUDPSock.sendto(data[expectedData[0]], addr)
            tmpUDPSock.close()

    def get_list_of_files(self):
        mypath = "files"
        onlyfiles = [f for f in listdir(mypath) if isfile(join(mypath, f))]
        return onlyfiles

    def __repr__(self):
        return "Server(host={}, port={})".format(self.host, self.port)

    def calculate_checksum(self, data):
        checksum = 0
        for byte in data:
            checksum += byte
        checksum = checksum % 256
        return checksum

    def split(self, path, buffer):
        path = "files/" + path
        list = []
        f = open(path, "rb")
        l = f.read(buffer)
        i = 0
        while l:
            l = str(i).encode() + "~".encode() + str(self.calculate_checksum(l)).encode() + "~".encode() + l
            list.append(l)
            l = f.read(buffer)
            i += 1
        f.close()
        return list, len(list)

if __name__ == '__main__':

    s = MyServer(HOST, PORT)
    s.accept_clients()
