# 1. Boot in Rommon
# 2. flash_init
# 3. rename flash:config.text flash:config.old
# 4. boot

# Once booted, run the following commands to remove the old vlans

# 1. erase startup-config
# 2. delete flash:vlan.dat
# 3. reload

import serial
import serial.tools.list_ports

def list_serial_ports():
    ports = list(serial.tools.list_ports.comports())
    if not ports:
        print("No serial ports found.")
        return []
    print("\Available serial ports:")
    for i,port in enumerate(ports):
        print(f"{i}: {port.device} - {port.description}")
    return ports

if __name__ == "__main__":
    ports = list_serial_ports()
    if not ports:
        exit(1)
        
    choice = input("\nSelect the serial port number: ").strip()
    try:
        idx = int(choice) - 1
        selected_port = ports[idx].device
    except (ValueError, IndexError):
        print("Invalid selection.")
        exit(1)