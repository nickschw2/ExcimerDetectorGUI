# Maximum number of detectors
N = 6

single_variables = {'pcb_revision': 'PCB Revision',
                    'pcb_serial': 'PCB Serial',
                    'logic_revision': 'Logic Revision',
                    'firmware_revision': 'Firmware Revision',
                    'temperature': 'Temperature (C)',
                    'bias_value': 'Bias Voltage (V)',
                    'bias_current': 'Bias Current (uA)',
                    'ref_voltage': 'Ref. Voltage (V)'}

threshold_variables = {f'threshold_{i + 1}': f'Threshold {i + 1}' for i in range(N)}
temp_variables = {f'temp_{i + 1}': f'Temp. Det. {i + 1} (C)' for i in range(N)}
press_variables = {f'press_{i + 1}': f'Press. Det. {i + 1} (mbar)' for i in range(N)}
status_variables = dict(single_variables)
status_variables.update(threshold_variables)
status_variables.update(temp_variables)
status_variables.update(press_variables)


# Widget display constants
userInputWidth = 8
labelPadding = 5 #pixels
framePadding = 15 #pixels

# Styles
themename = 'darkly'
button_opts = {'font':('Helvetica', 12), 'state':'normal'}
text_opts = {'font':('Helvetica', 12)}
entry_opts = {'font':('Helvetica', 12)}
# frame_opts = {'font':('Helvetica', 12), 'borderwidth': 3, 'relief': 'raised', 'padding': 12}
frame_opts = {'borderwidth': 3, 'relief': 'flat', 'padding': 12}