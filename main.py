# 1. Boot in Rommon
# 2. flash_init
# 3. rename flash:config.text flash:config.old
# 4. boot

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

if __name__ == "__main__":
    ports = list_serial_ports()
    idx = int(input("Select the serial port number: ").strip())
    selected_port = ports[idx].device
    check_rommon_prompt(selected_port)

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


send_flash_init(selected_port)
rename_flash_config(selected_port)
boot(selected_port)


# Once booted, run the following commands to remove the old vlans and finis the reset;

# 1. wait for the device to boot completely
# 2. erase startup-config
# 3. delete flash:vlan.dat
# 4. reload