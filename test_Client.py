import threading
import time
from os import listdir
from os.path import isfile, join
from unittest import TestCase

from new.Client import Client
from new.MyServer import MyServer


class TestClient(TestCase):

    def test_init(self):
        HOST = '127.0.0.1'
        PORT = 5002
        s = MyServer(HOST, PORT)
        s.accept_clients()

    def test_send_message(self):

        t1 = threading.Thread(target=self.test_init)
        t1.daemon = True
        t1.start()
        c1 = Client('nir')
        c2 = Client('hagai')
        time.sleep(0.2)
        t2 = threading.Thread(target=c1.send_message_prop, args=('hagai', 'hello'))
        t2.daemon = True
        t2.start()
        time.sleep(0.2)
        self.assertEqual(3, len(c2.list_of_messages))
        check = c2.list_of_messages[2].split(':')
        check = check[len(check) - 1][:-5]
        self.assertEqual('hello', check)

    def test_listen_for_messages(self):
        t1 = threading.Thread(target=self.test_init)
        t1.daemon = True
        t1.start()

        c1 = Client('nir') # The constructor of the client will start listening for messages() as a thread

        time.sleep(0.5)

        self.assertEqual(2, len(c1.list_of_messages))
        self.assertEqual('username accepted', c1.list_of_messages[0])
        self.assertEqual('<connected>', c1.list_of_messages[1])

        print(c1.list_of_messages)

    def test_get_file(self):
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

        t3 = threading.Thread(target=c1.send_message_prop, args=('<download><text.txt>',)) # This command will start get file method
        t3.daemon = True
        t3.start()

        time.sleep(0.2)

        self.assertEqual(c1.list_of_messages[len(c1.list_of_messages) - 1], "end_of_file")
        mypath = "..//new"
        onlyfiles = [f for f in listdir(mypath) if isfile(join(mypath, f))]


