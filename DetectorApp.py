import ttkbootstrap as ttk
from ttkbootstrap import validation
import numpy as np
import sys
import glob
import serial
from config import *
from visa_comms import ExcimerDetectorController

# Main app
class ExcimerDetectorApp(ttk.Window):
    def __init__(self):
        # Define style of app
        super().__init__(themename=themename)
        style = ttk.Style()
        self.colors = style.colors

        style.configure('TButton', **button_opts)
        style.configure('TFrame', **frame_opts)
        style.configure('TLabelframe.Label', **text_opts)
        style.configure('TEntry', **entry_opts)
        style.configure('TLabel', **text_opts)
        style.configure('TRadiobutton', **text_opts)
        style.configure('TNotebook.Tab', **text_opts)
        style.configure('TCheckbutton', **text_opts)
        self.option_add('*TCombobox*Listbox.font', text_opts)
        
        # Special code for styling big buttons
        style.configure('bigRed.TButton', font=(None, 24,), justify='center', background=self.colors.danger)
        style.configure('bigOrange.TButton', font=(None, 24,), justify='center', background=self.colors.warning)
        style.map('bigRed.TButton', background=[('active', '#e74c3c')])
        style.map('bigOrange.TButton', background=[('active', '#f39c12')])

        # Create and show user interface
        self.init_visaInstruments()
        self.configure_ui()
        self.serial_connect()
        self.init_ui()

    def configure_ui(self):
        # set title
        self.title('Excimer Detector App')

        # This line of code is customary to quit the application when it is closed
        self.protocol('WM_DELETE_WINDOW', self.on_closing)

        ### VISA CONNECTION SECTION ###
        connectionFrame = ttk.LabelFrame(self, text='Connection', bootstyle='primary')
        connectionFrame.grid(row=0, column=0, padx=framePadding, pady=framePadding)

        serial_ports = self.serial_ports()
        if len(serial_ports) == 0:
            self.print('No serial devices detected')
            self.on_closing()

        # Create a combobox for choosing the com port
        self.comCombobox = ttk.Combobox(connectionFrame, value=serial_ports, state='readonly', bootstyle='primary', **text_opts)
        self.comCombobox.current(0)
        self.comCombobox.bind('<<ComboboxSelected>>', self.serial_connect)
        self.comCombobox.pack(side='top', padx=labelPadding, pady=labelPadding)

        # Label to tell user whether detector is connected
        self.connectedString = ttk.StringVar()
        self.connectedString.set('Not connected')
        self.connectedLabel = ttk.Label(connectionFrame, textvariable=self.connectedString)
        self.connectedLabel.pack(side='top', padx=labelPadding, pady=labelPadding)

        ### USER INPUTS SECTION ###
        userInputFrame = ttk.LabelFrame(self, text='User Inputs', bootstyle='primary')
        userInputFrame.grid(row=0, column=1, padx=framePadding, pady=framePadding)

        self.calibration_bool = ttk.BooleanVar()
        self.bias_bool = ttk.BooleanVar()

        self.calibration_toggle_label = ttk.Label(userInputFrame, text='Calibration On')
        self.calibration_toggle = ttk.Checkbutton(userInputFrame, variable=self.calibration_bool, bootstyle='round-toggle')
        self.bias_toggle_label = ttk.Label(userInputFrame, text='Bias On')
        self.bias_toggle = ttk.Checkbutton(userInputFrame, variable=self.bias_bool, bootstyle='round-toggle')
        self.bias_label = ttk.Label(userInputFrame, text='Bias Voltage (V)')
        self.bias_entry = ttk.Entry(userInputFrame, width=userInputWidth, font=('Helvetica', 12))
        self.setValues_button = ttk.Button(userInputFrame, command=self.setDetectorValues, text='Set Values')
        
        self.calibration_toggle_label.grid(row=0, column=0, sticky='w', padx=labelPadding, pady=labelPadding)
        self.calibration_toggle.grid(row=0, column=1, sticky='w', padx=labelPadding, pady=labelPadding)
        self.bias_toggle_label.grid(row=1, column=0, sticky='w', padx=labelPadding, pady=labelPadding)
        self.bias_toggle.grid(row=1, column=1, sticky='w', padx=labelPadding, pady=labelPadding)
        self.bias_label.grid(row=2, column=0, sticky='w', padx=labelPadding, pady=labelPadding)
        self.bias_entry.grid(row=2, column=1, sticky='w', padx=labelPadding, pady=labelPadding)
        self.setValues_button.grid(row=5, column=0, sticky='w', padx=labelPadding, pady=labelPadding)

        # Create threshold entries
        self.thresholdEntries = {}
        for i in range(N):
            label = ttk.Label(userInputFrame, text=f'Threshold Val {i + 1}')
            entry = ttk.Entry(userInputFrame, width=userInputWidth, font=('Helvetica', 12))

            self.thresholdEntries[f'threshold_{i + 1}'] = entry
            label.grid(row=i, column=2, sticky='e', padx=labelPadding, pady=labelPadding)
            entry.grid(row=i, column=3, sticky='w', padx=labelPadding, pady=labelPadding)
            validation.add_range_validation(entry, 0, 2047, when='focus')

        ### STATUS SECTION ###
        statusFrame = ttk.LabelFrame(self, text='Status', bootstyle='primary')
        statusFrame.grid(row=1, column=0, columnspan=2, padx=framePadding, pady=framePadding)

        # I separated status variables into those that only exist for a controller and those that
        # have values for all N detectors
        self.status_values = {}
        M = len(single_variables)
        for i, (variable, name) in enumerate(status_variables.items()):
            str_var = ttk.StringVar()
            label = ttk.Label(statusFrame, text=f'{name}:')
            value = ttk.Label(statusFrame, textvariable=str_var)
            self.status_values[variable] = str_var

            if i < M:
                label.grid(row=i, column=0, sticky='e', padx=(labelPadding, 0), pady=labelPadding)
                value.grid(row=i, column=1, sticky='w', padx=(0, labelPadding), pady=labelPadding)
            else:
                label.grid(row=(i - (M - N)) % N, column=2 * int((i - (M - N)) / N), sticky='e', padx=(labelPadding, 0), pady=labelPadding)
                value.grid(row=(i - (M - N)) % N, column=2 * int((i - (M - N)) / N) + 1, sticky='w', padx=(0, labelPadding), pady=labelPadding)

        updateStatusButton = ttk.Button(statusFrame, command=self.set_status, text='Update Status')
        updateStatusButton.grid(row=M - 1, column=2, columnspan=6, pady=labelPadding)

    def init_ui(self):        
        # If the user closes out of the application during a wait_window, no extra windows pop up
        self.update()

        # center the app
        self.center_app()

    def serial_ports(self):
        """ Lists serial port names

            :raises EnvironmentError:
                On unsupported or unknown platforms
            :returns:
                A list of the serial ports available on the system
        """
        if sys.platform.startswith('win'):
            ports = ['COM%s' % (i + 1) for i in range(256)]
        elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
            # this excludes your current terminal "/dev/tty"
            ports = glob.glob('/dev/tty[A-Za-z]*')
        elif sys.platform.startswith('darwin'):
            ports = glob.glob('/dev/tty.*')
        else:
            raise EnvironmentError('Unsupported platform')

        result = []
        for port in ports:
            try:
                s = serial.Serial(port)
                s.close()
                result.append(port)
            except (OSError, serial.SerialException):
                pass
        return result
    
    def serial_connect(self, event=None):
        # Get the value of the COM port from the combobox and extract just the number at the end
        com = self.comCombobox.get()
        port = com[3:]
        connected = self.excimerDetectorController.connectInstrument(port)

        # If connected, set the status of the controller
        if connected:
            self.connectedString.set('Connected!')
            self.set_status()
        else:
            self.connectedString.set('Not connected')

    # Some geometry to center the app on the screen
    def center_app(self):
        self.update_idletasks()
        width = self.winfo_width()
        frm_width = self.winfo_rootx() - self.winfo_x()
        win_width = width + 2 * frm_width
        height = self.winfo_height()
        titlebar_height = self.winfo_rooty() - self.winfo_y()
        win_height = height + titlebar_height + frm_width
        x = self.winfo_screenwidth() // 2 - win_width // 2
        y = self.winfo_screenheight() // 2 - win_height // 2
        self.geometry(f'+{x}+{y}')
        self.deiconify()

    # Initialize the controller
    def init_visaInstruments(self):
        self.excimerDetectorController = ExcimerDetectorController()

    # Set the value for all status variables
    def set_status(self):
        connected = self.excimerDetectorController.read_controller()
        if connected:
            self.connectedString.set('Connected!')
            for variable, value in self.status_values.items():
                value.set(getattr(self.excimerDetectorController, variable))
        else:
            self.connectedString.set('Not connected')
    
    # Read user inputs and write command to controller
    def setDetectorValues(self):
        calibration = self.calibration_bool.get()
        bias = self.bias_bool.get()
        bias_string = self.bias_entry.get()
        bias_value = float(bias_string) if bias_string else 0
        threshold = [0] * N
        for variable, entry in self.thresholdEntries.items():
            num = int(variable.split('_')[1])
            string = entry.get()
            val = float(string) if string else 0
            threshold[num - 1] = val

        self.excimerDetectorController.write_command(calibration=calibration, bias=bias, bias_value=bias_value, threshold=threshold)
        self.set_status()

        
    # Special function for closing the window and program
    def on_closing(self):
        # Cancel all scheduled callbacks
        for after_id in self.tk.eval('after info').split():
            self.after_cancel(after_id)

        # If detector is connected, reset it back to default before closing
        if hasattr(self.excimerDetectorController, 'inst'):
            self.excimerDetectorController.write_command(calibration=False, bias=False, bias_value=0, threshold=[0] * N)

        self.quit()
        self.destroy()

# Loop that actually runs the code
if __name__ == "__main__":
    app = ExcimerDetectorApp()
    app.mainloop()