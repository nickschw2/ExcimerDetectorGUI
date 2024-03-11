import ttkbootstrap as ttk
from ttkbootstrap import validation
import numpy as np
from config import *
from visa_comms import ExcimerDetectorController


class ExcimerDetectorApp(ttk.Window):
    def __init__(self):
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
        self.init_ui()

    def configure_ui(self):
        # set title
        self.title('Excimer Detector App')

        # This line of code is customary to quit the application when it is closed
        self.protocol('WM_DELETE_WINDOW', self.on_closing)

        ### USER INPUTS SECTION ###
        # There are two columns of user inputs
        userInputFrame = ttk.LabelFrame(self, text='User Inputs', bootstyle='primary')
        userInputFrame.pack(side='left', padx=framePadding, pady=framePadding)

        self.calibration_bool = ttk.BooleanVar()
        self.bias_bool = ttk.BooleanVar()

        self.calibration_toggle_label = ttk.Label(userInputFrame, text='Calibration On')
        self.calibration_toggle = ttk.Checkbutton(userInputFrame, variable=self.calibration_bool, bootstyle='round-toggle')
        self.bias_toggle_label = ttk.Label(userInputFrame, text='Bias On')
        self.bias_toggle = ttk.Checkbutton(userInputFrame, variable=self.bias_bool, bootstyle='round-toggle')
        self.bias_label = ttk.Label(userInputFrame, text='Bias Voltage (V)')
        self.bias_entry = ttk.Entry(userInputFrame, width=userInputWidth)
        self.setValues_button = ttk.Button(userInputFrame, command=self.setDetectorValues, text='Set Values')
        
        self.calibration_toggle_label.grid(row=0, column=0, sticky='w', padx=labelPadding, pady=labelPadding)
        self.calibration_toggle.grid(row=0, column=1, sticky='w', padx=labelPadding, pady=labelPadding)
        self.bias_toggle_label.grid(row=1, column=0, sticky='w', padx=labelPadding, pady=labelPadding)
        self.bias_toggle.grid(row=1, column=1, sticky='w', padx=labelPadding, pady=labelPadding)
        self.bias_label.grid(row=2, column=0, sticky='w', padx=labelPadding, pady=labelPadding)
        self.bias_entry.grid(row=2, column=1, sticky='w', padx=labelPadding, pady=labelPadding)
        self.setValues_button.grid(row=5, column=0, sticky='w', padx=labelPadding, pady=labelPadding)

        self.thresholdEntries = {}
        for i in range(N):
            label = ttk.Label(userInputFrame, text=f'Threshold Val {i + 1}')
            entry = ttk.Entry(userInputFrame, width=userInputWidth, font=('Helvetica', 12))

            self.thresholdEntries[f'threshold_{i + 1}'] = entry
            label.grid(row=i, column=2, sticky='e', padx=labelPadding, pady=labelPadding)
            entry.grid(row=i, column=3, sticky='w', padx=labelPadding, pady=labelPadding)
            validation.add_range_validation(entry, 2048, 4096, when='focus')

        ### STATUS SECTION ###
        statusFrame = ttk.LabelFrame(self, text='Status', bootstyle='primary')
        statusFrame.pack(side='left', padx=framePadding, pady=framePadding)

        self.status_values = {}
        M = len(single_variables)
        for i, (variable, name) in enumerate(status_variables.items()):
            str_var = ttk.StringVar()
            label = ttk.Label(statusFrame, text=f'{name}:')
            value = ttk.Label(statusFrame, textvariable=str_var)
            self.status_values[variable] = str_var

            if i < M:
                label.grid(row=i, column=0, sticky='e', padx=labelPadding, pady=labelPadding)
                value.grid(row=i, column=1, sticky='w', padx=labelPadding, pady=labelPadding)
            else:
                label.grid(row=(i - (M - N)) % N, column=2 * int((i - (M - N)) / N), sticky='e', padx=labelPadding, pady=labelPadding)
                value.grid(row=(i - (M - N)) % N, column=2 * int((i - (M - N)) / N) + 1, sticky='w', padx=labelPadding, pady=labelPadding)

        updateStatusButton = ttk.Button(statusFrame, command=self.set_status, text='Update Status')
        updateStatusButton.grid(row=M - 1, column=2, columnspan=6)

    def init_ui(self):
        # center the app
        self.center_app()
        
        # If the user closes out of the application during a wait_window, no extra windows pop up
        self.update()

        self.set_status()

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
        self.geometry(f'+{x}+{0}')
        self.deiconify()

    def init_visaInstruments(self):
        self.excimerDetectorController = ExcimerDetectorController()

    def set_status(self):
        self.excimerDetectorController.read_controller()
        for variable, value in self.status_values.items():
            value.set(getattr(self.excimerDetectorController, variable))

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

        self.quit()
        self.destroy()

if __name__ == "__main__":
    app = ExcimerDetectorApp()
    app.mainloop()