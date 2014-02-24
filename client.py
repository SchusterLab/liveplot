import json
import warnings
from PyQt4 import QtNetwork
import numpy as np

__author__ = 'phil'


class LivePlotClient(QtNetwork.QLocalSocket):
    def __init__(self):
        super(LivePlotClient, self).__init__()
        self.connectToServer("LivePlotter")
        if not self.waitForConnected(1000):
            raise EnvironmentError("Couldn't find LivePlotter instance")
        self.disconnected.connect(self.disconnect_received)
        self.is_connected = True

    def send_to_plotter(self, meta, arr=None):
        if not self.is_connected:
            return
        if arr is not None:
            arrbytes = bytearray(arr)
            meta['arrsize'] = len(arrbytes)
        else:
            meta['arrsize'] = 0
        bytes = bytearray(json.dumps(meta))
        if len(bytes) > 200:
            print meta
            raise ValueError('Meta length exceeds maximum of 200')
        bytes = bytes.ljust(200, '\x00')
        if arr is not None:
            bytes.extend(arrbytes)
        for n in range(int(np.ceil(len(bytes)/8192.))):
            interval = bytes[n*8192:min((n+1)*8192, len(bytes))]
            self.write(interval)
            self.waitForBytesWritten(1000)


    def plot_y(self, name, arr):
        arr = np.array(arr)
        meta = {
            'name': name,
            'dtype': str(arr.dtype),
            'shape': arr.shape,
            'operation':'plot_y',
            'rank': 1,
        }
        self.send_to_plotter(meta, arr)

    def plot_z(self, name, arr):
        arr = np.array(arr)
        meta = {
            'name': name,
            'dtype': str(arr.dtype),
            'shape': arr.shape,
            'operation':'plot_z',
            'rank': 2,
        }
        self.send_to_plotter(meta, arr)

    def plot_xy(self, name, xs, ys):
        arr = np.array([xs, ys])
        meta = {
            'name': name,
            'dtype': str(arr.dtype),
            'shape': arr.shape,
            'operation':'plot_xy',
            'rank': 1,
        }
        self.send_to_plotter(meta, np.array([xs, ys]))

    def append_y(self, name, point):
        self.send_to_plotter({
            'name': name,
            'operation':'append_y',
            'value': point,
            'rank': 1,
        })

    def append_xy(self, name, x, y):
        self.send_to_plotter({
            'name': name,
            'operation':'append_xy',
            'value': (x, y),
            'rank': 1,
        })

    def clear(self, name):
        self.send_to_plotter({
            'name':name,
            'operation':'clear'
        })

    def disconnect_received(self):
        self.is_connected = False
        warnings.warn('Disconnected from LivePlotter server, plotting has been disabled')