import threading
import time
from unittest import TestCase

from new.Client import Client
from new.MyServer import MyServer


class TestMyServer(TestCase):
    global c1


    def test_accept_clients(self):

        HOST = "127.0.0.1"
        PORT = 5002

        s = MyServer(HOST, PORT)

        self.assertEqual(s.client_count, 0)

        t2 = threading.Thread(target=s.accept_clients)
        t2.daemon = True
        t2.start()

        time.sleep(0.2)

        c1 = Client('h')
        c2 = Client('g')

        time.sleep(0.2)

        self.assertEqual(s.client_count, 2)
        self.assertIsNotNone(s.dict_of_users['h'])
        self.assertIsNotNone(s.dict_of_users['g'])

    def test_handle_client(self):
        HOST = "127.0.0.1"
        PORT = 5002

        s = MyServer(HOST, PORT)

        self.assertEqual(s.client_count, 0)

        t2 = threading.Thread(target=s.accept_clients)
        t2.daemon = True
        t2.start()

        time.sleep(0.2)

        c1 = Client('h')
        c2 = Client('g')

        time.sleep(0.2)

        self.assertEqual(s.client_count, 2)
        self.assertIsNotNone(s.dict_of_users['h'])
        self.assertIsNotNone(s.dict_of_users['g'])

    def test_send_file_and_handle_udp(self):

        HOST = "127.0.0.1"
        PORT = 5002

        s = MyServer(HOST, PORT)

        self.assertEqual(s.client_count, 0)

        t2 = threading.Thread(target=s.accept_clients)
        t2.daemon = True
        t2.start()

        time.sleep(0.2)

        c1 = Client('h')

        time.sleep(0.2)

        t3 = threading.Thread(target=c1.send_message_prop, args=('<download><text.txt>',))
        t3.daemon = True
        t3.start()

        time.sleep(0.2)

        self.assertEqual(c1.list_of_messages[len(c1.list_of_messages) - 1], "end_of_file")

    def test_get_list_of_files(self):

        HOST = '127.0.0.1'
        PORT = 5002
        s = MyServer(HOST, PORT)
        self.assertEqual(['bigfile.txt', 'test.txt', 'text.txt'], s.get_list_of_files())
        self.assertEqual(3, len(s.get_list_of_files()))

    def test_split(self):

        HOST = '127.0.0.1'
        PORT = 5002
        file_name = 'test.txt'
        s = MyServer(HOST, PORT)
        self.assertEqual([b'0~97~a', b'1~99~c', b'2~98~b', b'3~100~d'], s.split(file_name, 1)[0])
        self.assertEqual(4, s.split(file_name, 1)[1])
        self.assertEqual(2, s.split(file_name, 2)[1])