import unittest
from sendData import on_mission_download

from socketIO_client_nexus import SocketIO, BaseNamespace


class TestSendData(unittest.TestCase):
    def test_on_mission_download(self):
        self.assertIsNotNone(on_mission_download(3))


if __name__ == '__main__':
    unittest.main()