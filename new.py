# new_fixed_v2.py

import serial
import serial.tools.list_ports
import time
import re # We need the 're' module to find the filename

# --- Helper Functions (No changes here) ---

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
        print(f"\rKeep holding the MODE button... {i} seconds remaining", end="", flush=True)
        time.sleep(1)
    
    print("\n\nYou can release the MODE button now!")
    print("The switch should now be entering ROMMON mode (the prompt will be 'switch:')...")
    print("="*60)

# --- Core Interaction Logic (No changes here) ---

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

# --- Main Script Logic (With updates) ---

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
            
            # <<< --- NEW STEP: Inspect Flash and Find IOS Image --- >>>
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

            # <<< --- MODIFIED STEP: Boot --- >>>
            print("\n" + "-"*20 + " Step 4: Boot " + "-"*20)
            # We will now boot the specific file we found, which is more reliable.
            boot_command = f"boot flash:{ios_image}"
            print(f"Executing explicit boot command: {boot_command}")
            
            boot_output = send_command(ser, boot_command, "enter the initial configuration dialog", timeout=400)
            if boot_output is None:
                print("\n❌ Switch did not boot to the initial configuration dialog. The OS image might be corrupt.")
                exit()
            print("\n✅ Switch has booted successfully.")

            # --- POST-BOOT STAGE (The rest of the script is the same as before) ---
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
            final_boot_output = send_command(ser, None, "enter the initial configuration dialog", timeout=400)
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