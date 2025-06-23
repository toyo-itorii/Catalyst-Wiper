# 1. Choose the serial port connected to the device and wait for the ROMMON prompt.

# 2. flash_init
# 3. rename flash:config.text flash:config.old
# 4. boot
# Once booted, run the following commands to remove the old vlans and finis the reset;
# 1. wait for the device to boot completely
# Would you like to enter the initial configuration dialog? [yes/no]: no
# 2. Enable
# 3. erase startup-config
# Erasing the nvram filesystem will remove all configuration files! Continue? [confirm]

# 3. delete flash:vlan.dat
# Delete filename [vlan.dat]?
# Delete flash:/vlan.dat? [confirm]
# 4. reload
# Process with reload [confirm]
# Would you like to enter the initial configuration dialog? [yes/no]: no
# enable
# show running-config

import serial  # Import the pyserial library for serial communication
import serial.tools.list_ports  # Import the list_ports tool from pyserial to list available serial ports
import time  # Import the time library for sleep/delay functions

def list_serial_ports():
    ports = list(serial.tools.list_ports.comports())  # Get a list of all available serial ports
    for i, port in enumerate(ports):  # Iterate through the list of ports with their index
        print(f"{i}: {port.device} - {port.description}")  # Print the index, device name, and description of each port
    return ports  # Return the list of ports

def check_rommon_prompt(port, baudrate=9600, timeout=2):
    try:
        with serial.Serial(port, baudrate=baudrate, timeout=timeout) as ser:  # Open the serial port with specified parameters
            # Send newline to trigger prompt
            ser.write(b'\r\n')  # Send a carriage return and newline to the device to trigger a prompt
            time.sleep(1)  # Wait for 1 second to allow the device to respond
            output = ser.read(ser.in_waiting or 128).decode(errors='ignore')  # Read available bytes from the serial buffer and decode
            print(f"Output from device:\n{output}")  # Print the output received from the device
            if "switch:" in output.lower():  # Check if the ROMMON prompt is present in the output
                print("ROMMON prompt detected. Connected to the correct device.")  # Print confirmation if ROMMON prompt is detected
                return True  # Return True if ROMMON prompt is detected
            else:
                print("ROMMON prompt not detected. Check your connection or device state.")  # Print warning if ROMMON prompt is not detected
                return False  # Return False if ROMMON prompt is not detected
    except Exception as e:
        print(f"Error: {e}")  # Print any exception that occurs during serial communication
        return False  # Return False if an exception occurs

def send_flash_init(port, baudrate=9600, timeout=2):
    with serial.Serial(port, baudrate=baudrate, timeout=timeout) as ser:  # Open the serial port with specified parameters
        # Send the flash_init command
        ser.write(b'flash_init\r\n')  # Send the 'flash_init' command followed by carriage return and newline
        time.sleep(1)  # Wait for 1 second to allow the device to process the command
        output = ser.read(ser.in_waiting or 4096).decode(errors='ignore')  # Read available bytes from the serial buffer and decode
        print("Device output after flash_init:\n", output)  # Print the output received after sending 'flash_init'

def rename_flash_config(port, baudrate=9600, timeout=2):
    with serial.Serial(port, baudrate=baudrate, timeout=timeout) as ser:  # Open the serial port with specified parameters
        # Send the flash_init command
        ser.write(b'rename flash:config.text flash:config.old\r\n')  # Send the command to rename config.text to config.old
        time.sleep(1)  # Wait for 1 second to allow the device to process the command
        output = ser.read(ser.in_waiting or 4096).decode(errors='ignore')  # Read available bytes from the serial buffer and decode
        print("Device output after flash_init:\n", output)  # Print the output received after renaming the config file

def boot(port, baudrate=9600, timeout=2):
    with serial.Serial(port, baudrate=baudrate, timeout=timeout) as ser:  # Open the serial port with specified parameters
        # Send the flash_init command
        ser.write(b'boot\r\n')  # Send the 'boot' command followed by carriage return and newline
        time.sleep(1)  # Wait for 1 second to allow the device to process the command
        output = ser.read(ser.in_waiting or 4096).decode(errors='ignore')  # Read available bytes from the serial buffer and decode
        print("Device output after flash_init:\n", output)  # Print the output received after sending 'boot'

def delete_vlan_dat(port, baudrate=9600, timeout=2):
    """
    Sends the 'delete flash:vlan.dat' command to the device after it has booted.
    Automatically confirms all prompts from the device.
    Prints all output from the device.
    """
    with serial.Serial(port, baudrate=baudrate, timeout=timeout) as ser:  # Open the serial port with specified parameters
        # Send the delete command
        ser.write(b'delete flash:vlan.dat\r\n')  # Send the command to delete vlan.dat file
        time.sleep(1)  # Wait for 1 second to allow the device to process the command
        output = ser.read(ser.in_waiting or 4096).decode(errors='ignore')  # Read available bytes from the serial buffer and decode
        print("Device output after sending delete command:\n", output)  # Print the output after sending delete command

        # Confirm filename prompt if present
        if "Delete filename" in output or "delete filename" in output:  # Check if the device is asking to confirm the filename
            ser.write(b'\r\n')  # Send carriage return and newline to confirm the filename
            time.sleep(1)  # Wait for 1 second to allow the device to process the confirmation
            output2 = ser.read(ser.in_waiting or 4096).decode(errors='ignore')  # Read available bytes from the serial buffer and decode
            print("Device output after confirming filename:\n", output2)  # Print the output after confirming filename
            output += output2  # Append the new output to the previous output

        # Confirm [confirm] prompt if present
        if "[confirm]" in output or "confirm" in output.lower():  # Check if the device is asking for a final confirmation
            ser.write(b'\r\n')  # Send carriage return and newline to confirm the delete operation
            time.sleep(1)  # Wait for 1 second to allow the device to process the confirmation
            output3 = ser.read(ser.in_waiting or 4096).decode(errors='ignore')  # Read available bytes from the serial buffer and decode
            print("Device output after confirming delete:\n", output3)  # Print the output after confirming delete
            output += output3  # Append the new output to the previous output

        print("Final device output after deleting vlan.dat:\n", output)  # Print the final output after deleting vlan.dat

if __name__ == "__main__":  # Check if this script is being run as the main program
    ports = list_serial_ports()  # List all available serial ports and store them in 'ports'
    idx = int(input("Select the serial port number: ").strip())  # Ask the user to select a serial port by index
    selected_port = ports[idx].device  # Get the device name of the selected port
    check_rommon_prompt(selected_port)  # Check if the device is in ROMMON mode

send_flash_init(selected_port)  # Send the 'flash_init' command to the device
rename_flash_config(selected_port)  # Rename the config.text file to config.old
boot(selected_port)  # Boot the device

# Wait for the device to boot completely before running this
delete_vlan_dat(selected_port)  # Delete the vlan.dat file from the device