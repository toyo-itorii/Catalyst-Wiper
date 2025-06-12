#!/usr/bin/env python3
"""
Cisco C3750 Factory Reset Script for MobaXterm
Resets a password-locked Cisco C3750 switch via console connection

Requirements:
- MobaXterm with Python
- Console cable connected to switch
- Physical access to switch for power cycling

Usage:
1. Connect console cable to switch
2. Open MobaXterm terminal
3. Run: python cisco_reset.py
4. Follow the prompts
"""

import serial
import time
import sys
import threading
from serial.tools import list_ports

class CiscoReset:
    def __init__(self):
        self.ser = None
        self.reset_complete = False
        
    def list_com_ports(self):
        """List available COM ports"""
        ports = list_ports.comports()
        print("\nAvailable COM ports:")
        for i, port in enumerate(ports):
            print(f"{i+1}. {port.device} - {port.description}")
        return ports
    
    def connect_serial(self, port, baudrate=9600):
        """Connect to serial port"""
        try:
            self.ser = serial.Serial(
                port=port,
                baudrate=baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=1,
                xonxoff=False,
                rtscts=False,
                dsrdtr=False
            )
            print(f"Connected to {port} at {baudrate} baud")
            return True
        except Exception as e:
            print(f"Error connecting to {port}: {e}")
            return False
    
    def send_command(self, command, delay=1):
        """Send command to switch"""
        if self.ser and self.ser.is_open:
            print(f"Sending: {command}")
            self.ser.write((command + '\r\n').encode())
            time.sleep(delay)
    
    def send_break(self):
        """Send break signal"""
        if self.ser and self.ser.is_open:
            print("Sending BREAK signal...")
            self.ser.send_break(duration=0.5)
            time.sleep(0.5)
            self.ser.send_break(duration=0.5)
            time.sleep(1)
    
    def read_output(self, timeout=30):
        """Read output from switch with timeout"""
        start_time = time.time()
        output = ""
        
        while time.time() - start_time < timeout:
            if self.ser and self.ser.is_open and self.ser.in_waiting:
                try:
                    data = self.ser.read(self.ser.in_waiting).decode('utf-8', errors='ignore')
                    output += data
                    print(data, end='')
                except:
                    pass
            time.sleep(0.1)
        
        return output
    
    def wait_for_prompt(self, prompt, timeout=60):
        """Wait for specific prompt"""
        print(f"Waiting for prompt: '{prompt}'")
        start_time = time.time()
        output = ""
        
        while time.time() - start_time < timeout:
            if self.ser and self.ser.is_open and self.ser.in_waiting:
                try:
                    data = self.ser.read(self.ser.in_waiting).decode('utf-8', errors='ignore')
                    output += data
                    print(data, end='')
                    
                    if prompt.lower() in output.lower():
                        print(f"\nFound prompt: {prompt}")
                        return True
                except:
                    pass
            time.sleep(0.1)
        
        print(f"\nTimeout waiting for prompt: {prompt}")
        return False
    
    def factory_reset(self):
        """Perform factory reset sequence"""
        print("\n" + "="*50)
        print("CISCO C3750 FACTORY RESET SEQUENCE")
        print("="*50)
        
        print("\n1. Power cycle the switch NOW!")
        print("   - Unplug power cable")
        print("   - Wait 5 seconds")
        print("   - Plug power cable back in")
        
        input("\nPress ENTER when you've started the power cycle...")
        
        print("\n2. Waiting for boot sequence...")
        print("   Looking for 'Initializing Flash...' message")
        
        # Wait for initialization message and send break
        if self.wait_for_prompt("initializing flash", 120):
            print("\n3. Sending BREAK signal to enter ROMMON...")
            self.send_break()
            time.sleep(2)
            self.send_break()  # Send twice to ensure it works
        else:
            print("Did not detect initialization. Trying break signal anyway...")
            self.send_break()
        
        print("\n4. Waiting for switch: prompt...")
        if self.wait_for_prompt("switch:", 30):
            print("\n5. Initializing flash...")
            self.send_command("flash_init")
            time.sleep(3)
            
            print("\n6. Loading helper files...")
            self.send_command("load_helper")
            time.sleep(2)
            
            print("\n7. Listing flash contents...")
            self.send_command("dir flash:")
            time.sleep(2)
            
            print("\n8. Deleting VLAN database...")
            self.send_command("del flash:vlan.dat")
            if self.wait_for_prompt("(y/n)?", 10):
                self.send_command("y")
                time.sleep(1)
            
            print("\n9. Deleting configuration file...")
            self.send_command("del flash:config.text")
            if self.wait_for_prompt("(y/n)?", 10):
                self.send_command("y")
                time.sleep(1)
            
            print("\n10. Deleting private config (if exists)...")
            self.send_command("del flash:private-config.text")
            if self.wait_for_prompt("(y/n)?", 10):
                self.send_command("y")
                time.sleep(1)
            
            print("\n11. Booting switch with factory defaults...")
            self.send_command("boot")
            
            print("\n" + "="*50)
            print("FACTORY RESET INITIATED!")
            print("="*50)
            print("The switch will now boot with factory defaults.")
            print("This may take 2-3 minutes.")
            print("You can disconnect when you see the initial setup dialog.")
            
            # Monitor boot process
            print("\nMonitoring boot process (press Ctrl+C to stop)...")
            try:
                self.read_output(180)  # Monitor for 3 minutes
            except KeyboardInterrupt:
                print("\nMonitoring stopped by user.")
        else:
            print("Failed to enter ROMMON mode. Please try again.")
    
    def interactive_mode(self):
        """Interactive mode for manual commands"""
        print("\n" + "="*50)
        print("INTERACTIVE MODE")
        print("="*50)
        print("Type commands to send to switch.")
        print("Type 'exit' to quit.")
        print("Type 'break' to send break signal.")
        
        while True:
            try:
                cmd = input("\nCommand: ").strip()
                
                if cmd.lower() == 'exit':
                    break
                elif cmd.lower() == 'break':
                    self.send_break()
                elif cmd:
                    self.send_command(cmd)
                    time.sleep(1)
                    self.read_output(5)
                    
            except KeyboardInterrupt:
                break
    
    def run(self):
        """Main execution"""
        print("Cisco C3750 Factory Reset Tool")
        print("==============================")
        
        # List and select COM port
        ports = self.list_com_ports()
        if not ports:
            print("No COM ports found!")
            return
        
        try:
            choice = int(input(f"\nSelect COM port (1-{len(ports)}): ")) - 1
            selected_port = ports[choice].device
        except (ValueError, IndexError):
            print("Invalid selection!")
            return
        
        # Connect to serial port
        if not self.connect_serial(selected_port):
            return
        
        print(f"\nConnected to {selected_port}")
        print("Console connection established.")
        
        # Choose operation mode
        print("\nSelect operation:")
        print("1. Automatic factory reset")
        print("2. Interactive mode (manual commands)")
        
        try:
            choice = int(input("Choice (1-2): "))
        except ValueError:
            choice = 1
        
        try:
            if choice == 2:
                self.interactive_mode()
            else:
                self.factory_reset()
        except KeyboardInterrupt:
            print("\nOperation cancelled by user.")
        finally:
            if self.ser and self.ser.is_open:
                self.ser.close()
                print("\nSerial connection closed.")

def main():
    """Main function"""
    try:
        reset_tool = CiscoReset()
        reset_tool.run()
    except KeyboardInterrupt:
        print("\nProgram interrupted by user.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()