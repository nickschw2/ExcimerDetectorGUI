import pyvisa
import numpy as np
from config import *

class ExcimerDetectorController():
    def __init__(self):
        # Initialize visa resource manager
        self.rm = pyvisa.ResourceManager('@py')

    # Given a port number, connect to instrument using pyvisa
    def connectInstrument(self, port):
        instrumentName = f'ASRL{port}::INSTR'
        try:
            self.inst = self.rm.open_resource(instrumentName) # default values of baud rate, parity, etc are okay, but can change them here
        except pyvisa.errors.VisaIOError:
            return False
        
        connected = self.read_controller()
        if connected:
            print('Excimer detector controller has been initialized successfully.')

        return connected

    def read_controller(self):
        # Formulae for converting to meaningful numbers
        def data2volts(data):
            return np.array(data).astype(int) * 3.3 / 4095
        def data2temp(data):
            volts = data2volts(data)
            return np.round(((volts * 100) - 32) * 0.5555, 1)
        def data2bias(data):
            volts = data2volts(data)
            return np.round(volts * 33, 1)
        def data2current(data):
            volts = data2volts(data)
            return np.round(volts * 100, 1)
        def data2threshold(data):
            return np.array(data).astype(int) - 1508
        def data2pressure(data):
            volts = data2volts(data)
            return np.round((volts / 5.1 + 0.04) * 2500, 1)

        try:
            status = self.inst.query('1').strip().split(' ')
        except pyvisa.errors.VisaIOError:
            return False

        # Sometimes after a write, the length of status is just for the write values, so just run query again
        if len(status) != 50:
            status = self.inst.query('1').strip().split(' ')

        self.pcb_revision = status[0]
        self.pcb_serial = status[1]
        self.logic_revision = status[2]
        self.firmware_revision = status[3]
        self.temperature = data2temp(status[4])
        self.bias_value = data2bias(status[5])
        self.threshold = data2threshold(status[6:12])
        self.bias_current = data2current(status[12])
        self.ref_voltage = np.round(data2volts(status[13]), 1)
        self.detector_temps = data2temp(status[14:20])
        self.detector_press = data2pressure(status[20:26])
        self.data = status[26:50]

        # Set variables
        for i in range(6):
            setattr(self, f'threshold_{i + 1}', self.threshold[i])
            setattr(self, f'temp_{i + 1}', self.detector_temps[i])
            setattr(self, f'press_{i + 1}', self.detector_press[i])

        return True

    # Write command based off firmware
    def write_command(self, calibration=False, bias=True, bias_value=28, threshold=[220]*N):
        if bias_value > 30:
            bias_value = 30
            print('Cannot exceed bias voltage of more than 30 V')

        bias_value_digital = int(bias_value * 67.41)
        threshold_digital = [str(int(val + 1508)) for val in threshold]
        command = f'0 {int(calibration)} {int(bias)} {bias_value_digital} {" ".join(threshold_digital)}\r'
        self.inst.write(command)

        self.read_controller()