# Todo : fix the rommon part

# 1. Choose the serial port connected to the device and press physical rommon button.
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

def reboot_switch_with_rommon():
    """
    Guide the user through the physical reboot and ROMMON button process.
    """
    print("\n" + "="*60)
    print("SWITCH REBOOT AND ROMMON PROCESS")
    print("="*60)
    
    # Step 1: Reboot the switch
    input("\nStep 1: Press ENTER to continue, then physically reboot your switch...")
    print("Please reboot your switch now (unplug and plug back in, or use the power button)")
    
    # Step 2: ROMMON button timer
    print("\nStep 2: ROMMON Button Process")
    print("Get ready to press and hold the ROMMON button on your switch...")
    input("Press ENTER when you're ready to start the 10-second timer...")
    
    print("\nSTART PRESSING THE ROMMON BUTTON NOW!")
    print("Hold it down for the full 10 seconds...")
    
    # 10-second countdown timer
    for i in range(10, 0, -1):
        print(f"\rKeep holding ROMMON button... {i} seconds remaining", end="", flush=True)
        time.sleep(1)
    
    print("\n\nYou can release the ROMMON button now!")
    print("The switch should now be entering ROMMON mode...")
    print("="*60)

def check_rommon_prompt(port, baudrate=9600, timeout=2):
    """
    Continuously checks if the device is in ROMMON mode.
    No longer sends break signals - relies on physical ROMMON button.
    """
    try:
        with serial.Serial(port, baudrate=baudrate, timeout=timeout) as ser:  # Open the serial port
            print("\nWaiting for ROMMON prompt...")
            attempts = 0
            max_attempts = 30  # Wait up to 60 seconds (30 attempts * 2 seconds each)
            
            while attempts < max_attempts:  # Loop until ROMMON prompt is detected or timeout
                ser.write(b'\r\n')  # Send newline to trigger prompt
                time.sleep(2)  # Wait for device to respond
                output = ser.read(ser.in_waiting or 128).decode(errors='ignore')  # Read output
                
                if output.strip():  # Only print if there's actual output
                    print(f"Output from device:\n{output}")
                
                if "switch:" in output.lower():  # Check for ROMMON prompt
                    print("✓ ROMMON prompt detected. Connected to the correct device.")
                    return True  # Exit loop if ROMMON detected
                
                attempts += 1
                if attempts % 5 == 0:  # Print status every 10 seconds
                    print(f"Still waiting for ROMMON prompt... (attempt {attempts}/{max_attempts})")
            
            print("❌ ROMMON prompt not detected within timeout period.")
            print("Please ensure:")
            print("1. The switch was properly rebooted")
            print("2. The ROMMON button was held for the full 10 seconds during boot")
            print("3. The serial connection is working")
            return False

    except Exception as e:
        print(f"Error: {e}")
        return False

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
        print("Device output after rename config:\n", output)  # Print the output received after renaming the config file

def boot(port, baudrate=9600, timeout=2):
    with serial.Serial(port, baudrate=baudrate, timeout=timeout) as ser:  # Open the serial port with specified parameters
        # Send the boot command
        ser.write(b'boot\r\n')  # Send the 'boot' command followed by carriage return and newline
        time.sleep(1)  # Wait for 1 second to allow the device to process the command
        output = ser.read(ser.in_waiting or 4096).decode(errors='ignore')  # Read available bytes from the serial buffer and decode
        print("Device output after boot:\n", output)  # Print the output received after sending 'boot'

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
    
    # Guide user through reboot and ROMMON button process
    reboot_switch_with_rommon()
    
    # Check for ROMMON prompt
    if check_rommon_prompt(selected_port):
        print("\n" + "="*60)
        print("EXECUTING ROMMON COMMANDS")
        print("="*60)
        
        send_flash_init(selected_port)  # Send the 'flash_init' command to the device
        rename_flash_config(selected_port)  # Rename the config.text file to config.old
        boot(selected_port)  # Boot the device
        
        print("\n" + "="*60)
        print("ROMMON COMMANDS COMPLETED")
        print("Wait for the device to boot completely before running delete_vlan_dat")
        print("="*60)
        
        # Wait for the device to boot completely before running this
        input("\nPress ENTER when the device has finished booting...")
        delete_vlan_dat(selected_port)  # Delete the vlan.dat file from the device
    else:
        print("\n❌ Could not establish ROMMON connection. Please try again.")