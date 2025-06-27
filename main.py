# new_fixed_v3.py - Updated with microcode programming handling

import serial
import serial.tools.list_ports
import time
import re # We need the 're' module to find the filename

# --- Helper Functions ---

def list_serial_ports():
    """Gets and displays a list of available serial ports."""
    ports = list(serial.tools.list_ports.comports())
    print("Available serial ports:")
    if not ports:
        print("  No serial ports found. Please connect your adapter.")
    for i, port in enumerate(ports):
        print(f"  {i}: {port.device} - {port.description}")
    return ports

def reboot_switch_with_rommon():
    """Guides the user through the physical reboot and ROMMON entry process."""
    print("\n" + "="*60)
    print("SWITCH REBOOT AND ROMMON PROCESS")
    print("="*60)
    input("\nStep 1: Press ENTER, then physically reboot your switch (unplug and plug back in)...")
    print("\nStep 2: Get ready to press and hold the MODE button on your switch's front panel.")
    input("Press ENTER when you're ready to start the 15-second timer...")
    
    print("\nSTART PRESSING THE MODE BUTTON NOW!")
    print("Hold it down for the full 15 seconds...")
    
    for i in range(15, 0, -1):
        print(f"\rHold or press repeatedly the MODE button... {i} seconds remaining", end="", flush=True)
        time.sleep(1)
    
    print("\n\nYou can release the MODE button now!")
    print("The switch should now be entering ROMMON mode (the prompt will be 'switch:')...")
    print("="*60)

# --- Core Interaction Logic ---

def send_command(ser, command, expected_prompt, timeout=60, print_output=True):
    """
    Sends a command to the serial device and waits for an expected prompt,
    which indicates the command has finished.
    """
    if command is not None:
        ser.write(command.encode('utf-8') + b'\r\n')

    full_output = ""
    start_time = time.time()
    while time.time() - start_time < timeout:
        if ser.in_waiting > 0:
            time.sleep(0.5) 
            output = ser.read(ser.in_waiting).decode('utf-8', errors='ignore')
            if print_output:
                print(output, end='', flush=True)
            full_output += output
            if expected_prompt.lower() in full_output.lower():
                return full_output
        time.sleep(0.1)

    print(f"\n\n\n❌ TIMEOUT: Did not see the expected prompt '{expected_prompt}' within {timeout} seconds.")
    return None

def send_command_with_progress(ser, command, expected_prompt, timeout=60, show_progress=False):
    """
    Enhanced version of send_command that shows progress for long operations.
    """
    if command is not None:
        ser.write(command.encode('utf-8') + b'\r\n')

    full_output = ""
    start_time = time.time()
    last_progress = time.time()
    
    while time.time() - start_time < timeout:
        if ser.in_waiting > 0:
            time.sleep(0.5) 
            output = ser.read(ser.in_waiting).decode('utf-8', errors='ignore')
            print(output, end='', flush=True)
            full_output += output
            last_progress = time.time()  # Reset progress timer when we get output
            
            if expected_prompt.lower() in full_output.lower():
                return full_output
        else:
            # Show progress dots if no output for 30 seconds
            if show_progress and (time.time() - last_progress) > 30:
                elapsed = int(time.time() - start_time)
                print(f"\n[Still working... {elapsed//60}m {elapsed%60}s elapsed]", flush=True)
                last_progress = time.time()
        
        time.sleep(0.1)

    elapsed = int(time.time() - start_time)
    print(f"\n\n❌ TIMEOUT: Did not see '{expected_prompt}' within {timeout} seconds ({elapsed//60}m {elapsed%60}s elapsed).")
    return None

# --- Main Script Logic ---

if __name__ == "__main__":
    ports = list_serial_ports()
    if not ports:
        exit()
    
    selected_port = None
    while selected_port is None:
        try:
            idx_str = input("\nSelect the serial port number: ").strip()
            if not idx_str: continue
            idx = int(idx_str)
            selected_port = ports[idx].device
        except (ValueError, IndexError):
            print("❌ Invalid selection. Please enter a number from the list.")

    reboot_switch_with_rommon()

    try:
        with serial.Serial(selected_port, baudrate=9600, timeout=1) as ser:
            print(f"\n✅ Successfully opened port {selected_port}. Waiting for ROMMON prompt...")

            # --- ROMMON STAGE ---
            rommon_output = send_command(ser, "\r\n", "switch:", timeout=90)
            if rommon_output is None:
                print("\n❌ Could not detect ROMMON prompt. Please check the connection and reboot process, then try again.")
                exit()
            print("\n✅ ROMMON prompt detected. Starting commands.")

            # Step 1: flash_init
            print("\n" + "-"*20 + " Step 1: flash_init " + "-"*20)
            flash_init_output = send_command(ser, "flash_init", "switch:", timeout=120)
            if flash_init_output is None or "error" in flash_init_output.lower():
                print("\n❌ 'flash_init' command failed or timed out.")
                exit()
            print("\n✅ 'flash_init' completed.")

            # Step 2: Rename Config
            print("\n" + "-"*20 + " Step 2: Rename Config " + "-"*20)
            rename_cmd = "rename flash:config.text flash:config.old"
            rename_output = send_command(ser, rename_cmd, "switch:", timeout=30)
            if rename_output is None or "error" in rename_output.lower() or "invalid" in rename_output.lower():
                print("\n⚠️ 'rename' command failed, likely because config.text doesn't exist (this is OK).")
            else:
                print("\n✅ 'rename' command sent successfully.")
            
            # Step 3: Find IOS Image
            print("\n" + "-"*20 + " Step 3: Find IOS Image " + "-"*20)
            dir_output = send_command(ser, "dir flash:", "switch:", timeout=60)
            if dir_output is None:
                print("\n❌ Could not read the flash directory. The filesystem may be corrupt.")
                exit()
            
            # Use a regular expression (regex) to find a filename ending in .bin
            ios_image = None
            match = re.search(r"(\S+\.bin)", dir_output)
            if match:
                ios_image = match.group(1).strip()
                print(f"\n✅ Found IOS image file: {ios_image}")
            
            if not ios_image:
                print("\n❌ CRITICAL: No .bin file found in flash directory.")
                print("   The switch OS is missing or the flash is unreadable.")
                print("   You may need to use XMODEM to upload a new IOS image.")
                exit()

            # Step 4: Boot with Enhanced Microcode Handling
            print("\n" + "-"*20 + " Step 4: Boot " + "-"*20)
            boot_command = f"boot flash:{ios_image}"
            print(f"Executing explicit boot command: {boot_command}")
            
            # First, send the boot command and wait for microcode programming to start
            print("Sending boot command...")
            ser.write(boot_command.encode('utf-8') + b'\r\n')
            time.sleep(2)

            # Wait for microcode programming to begin
            print("Waiting for microcode programming to start...")
            microcode_start = send_command(ser, None, "Front-end Microcode IMG MGR", timeout=300)
            if microcode_start is None:
                print("\n⚠️ Microcode programming didn't start as expected. Continuing anyway...")
                # Try waiting directly for the config dialog
                boot_output = send_command_with_progress(ser, None, "enter the initial configuration dialog", timeout=4800, show_progress=True)
            else:
                print("\n✅ Microcode programming started. This may take 15-30 minutes...")
                print("Progress indicators: s=success, p=checkpoint, r=read, w=write")
                print("Please be patient - this is normal!")

                # Now wait for the microcode programming to complete
                # Look for signs that it's finished and moving to the next phase
                print("\nWaiting for microcode programming to complete...")
                microcode_complete = send_command_with_progress(ser, None, "Base ethernet MAC Address", timeout=4800, show_progress=True)
                if microcode_complete is None:
                    # If we don't see the MAC address message, try waiting for other boot messages
                    print("\nTrying alternative boot completion indicators...")
                    boot_output = send_command_with_progress(ser, None, "enter the initial configuration dialog", timeout=4800, show_progress=True)
                else:
                    # Continue waiting for the final prompt
                    print("\n✅ Microcode programming appears complete. Waiting for initial config dialog...")
                    boot_output = send_command_with_progress(ser, None, "enter the initial configuration dialog", timeout=4800, show_progress=True)

            if boot_output is None:
                print("\n❌ Switch boot process timed out. This could mean:")
                print("   1. The microcode programming is taking longer than expected")
                print("   2. There's a hardware issue with the switch")
                print("   3. The IOS image is corrupted")
                print("\nYou may need to wait longer or check the switch manually.")
                exit()

            print("\n✅ Switch has booted successfully.")

            # --- POST-BOOT STAGE ---
            print("\n" + "-"*20 + " Step 5: Initial Setup " + "-"*20)
            no_output = send_command(ser, "no", ">", timeout=30)
            if no_output is None:
                print("\n❌ Failed to answer 'no' to the initial config dialog.")
                exit()

            enable_output = send_command(ser, "enable", "#", timeout=30)
            if enable_output is None:
                print("\n❌ Failed to enter enable mode.")
                exit()
            print("\n✅ Successfully entered enable mode.")

            print("\n" + "-"*20 + " Step 6: Erase Startup Config " + "-"*20)
            erase_output = send_command(ser, "erase startup-config", "[confirm]", timeout=30)
            if erase_output is None:
                 print("\n❌ 'erase startup-config' command failed.")
                 exit()
            erase_confirm_output = send_command(ser, "\r\n", "#", timeout=30)
            if erase_confirm_output is None:
                 print("\n❌ Failed to confirm startup-config erase.")
                 exit()
            print("\n✅ Startup config erased.")

            print("\n" + "-"*20 + " Step 7: Delete vlan.dat " + "-"*20)
            vlan_output = send_command(ser, "delete flash:vlan.dat", "Delete filename [vlan.dat]?", timeout=15)
            if vlan_output and "delete filename" in vlan_output.lower():
                print("\nConfirming filename...")
                vlan_confirm1 = send_command(ser, "\r\n", "Delete flash:/vlan.dat? [confirm]", timeout=15)
                if vlan_confirm1:
                    print("\nConfirming deletion...")
                    vlan_confirm2 = send_command(ser, "\r\n", "#", timeout=15)
                    if vlan_confirm2:
                        print("\n✅ vlan.dat deleted.")
            elif vlan_output and ("no such file" in vlan_output.lower() or "#" in vlan_output):
                print("\nℹ️ vlan.dat does not exist. Skipping.")
            else:
                print("\n❌ Failed to delete vlan.dat.")

            print("\n" + "-"*20 + " Step 8: Reload " + "-"*20)
            reload_output = send_command(ser, "reload", "Proceed with reload? [confirm]", timeout=30)
            if reload_output is None:
                print("\n❌ 'reload' command failed.")
                exit()
            
            print("\nConfirming reload. The script will now monitor the reboot process...")
            ser.write(b'\r\n')
            time.sleep(5) 

            print("\n" + "-"*20 + " Step 9: Final Verification " + "-"*20)
            print("Waiting for final boot (this may take another 15-30 minutes for microcode programming)...")
            final_boot_output = send_command_with_progress(ser, None, "enter the initial configuration dialog", timeout=4800, show_progress=True) 
            if final_boot_output is None:
                print("\n❌ Switch did not reload correctly.")
                exit()

            final_no_output = send_command(ser, "no", ">", timeout=30)
            if final_no_output is None:
                print("\n❌ Failed to answer 'no' to the final config dialog.")
                exit()

            final_enable_output = send_command(ser, "enable", "#", timeout=30)
            if final_enable_output is None:
                print("\n❌ Failed to enter final enable mode.")
                exit()

            print("\n\n" + "="*60)
            print("✅ ✅ ✅ SWITCH RESET COMPLETE! ✅ ✅ ✅")
            print("The switch is now in enable mode with a blank configuration.")
            print("="*60)

    except serial.SerialException as e:
        print(f"\n❌ Serial Port Error: {e}")
        print("Please ensure the correct port is selected and no other program is using it.")
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")