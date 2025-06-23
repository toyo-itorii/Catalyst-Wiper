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


import serial
import serial.tools.list_ports
import time

def list_serial_ports():
    ports = list(serial.tools.list_ports.comports())
    for i, port in enumerate(ports):
        print(f"{i}: {port.device} - {port.description}")
    return ports

def check_rommon_prompt(port, baudrate=9600, timeout=2):
    try:
        with serial.Serial(port, baudrate=baudrate, timeout=timeout) as ser:
            # Send newline to trigger prompt
            ser.write(b'\r\n')
            time.sleep(1)
            output = ser.read(ser.in_waiting or 128).decode(errors='ignore')
            print(f"Output from device:\n{output}")
            if "switch:" in output.lower():
                print("ROMMON prompt detected. Connected to the correct device.")
                return True
            else:
                print("ROMMON prompt not detected. Check your connection or device state.")
                return False
    except Exception as e:
        print(f"Error: {e}")
        return False

def send_flash_init(port, baudrate=9600, timeout=2):
    with serial.Serial(port, baudrate=baudrate, timeout=timeout) as ser:
        # Send the flash_init command
        ser.write(b'flash_init\r\n')
        time.sleep(1)  # Wait for device to process
        output = ser.read(ser.in_waiting or 4096).decode(errors='ignore')
        print("Device output after flash_init:\n", output)

def rename_flash_config(port, baudrate=9600, timeout=2):

    with serial.Serial(port, baudrate=baudrate, timeout=timeout) as ser:
        # Send the flash_init command
        ser.write(b'rename flash:config.text flash:config.old\r\n')
        time.sleep(1)  # Wait for device to process
        output = ser.read(ser.in_waiting or 4096).decode(errors='ignore')
        print("Device output after flash_init:\n", output)

def boot(port, baudrate=9600, timeout=2):

    with serial.Serial(port, baudrate=baudrate, timeout=timeout) as ser:
        # Send the flash_init command
        ser.write(b'boot\r\n')
        time.sleep(1)  # Wait for device to process
        output = ser.read(ser.in_waiting or 4096).decode(errors='ignore')
        print("Device output after flash_init:\n", output)

def delete_vlan_dat(port, baudrate=9600, timeout=2):
    """
    Sends the 'delete flash:vlan.dat' command to the device after it has booted.
    Automatically confirms all prompts from the device.
    Prints all output from the device.
    """
    with serial.Serial(port, baudrate=baudrate, timeout=timeout) as ser:
        # Send the delete command
        ser.write(b'delete flash:vlan.dat\r\n')
        time.sleep(1)
        output = ser.read(ser.in_waiting or 4096).decode(errors='ignore')
        print("Device output after sending delete command:\n", output)

        # Confirm filename prompt if present
        if "Delete filename" in output or "delete filename" in output:
            ser.write(b'\r\n')
            time.sleep(1)
            output2 = ser.read(ser.in_waiting or 4096).decode(errors='ignore')
            print("Device output after confirming filename:\n", output2)
            output += output2

        # Confirm [confirm] prompt if present
        if "[confirm]" in output or "confirm" in output.lower():
            ser.write(b'\r\n')
            time.sleep(1)
            output3 = ser.read(ser.in_waiting or 4096).decode(errors='ignore')
            print("Device output after confirming delete:\n", output3)
            output += output3

        print("Final device output after deleting vlan.dat:\n", output)

if __name__ == "__main__":
    ports = list_serial_ports()
    idx = int(input("Select the serial port number: ").strip())
    selected_port = ports[idx].device
    check_rommon_prompt(selected_port)

send_flash_init(selected_port)
rename_flash_config(selected_port)
boot(selected_port)

# Wait for the device to boot completely before running this
delete_vlan_dat(selected_port)