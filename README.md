![image](https://github.com/user-attachments/assets/45a5ab9d-e485-4a1d-b5e7-534229120baf)

<!-- Make the Readme more technical looking -->

# Catalyst Wiper

A Python script to perform factory reset operations on Cisco Catalyst switches via serial connection.

## ⚠️ WARNING

**This tool performs destructive operations that will completely erase all configuration data from target switches. Use with extreme caution and ensure you have proper authorization before running.**

## Features

- Automated factory reset for Cisco Catalyst switches
- Support for multiple switch models (2960, 3560, 3750, 9300 series, etc.)
- Batch processing for multiple switches
- Detailed logging and progress tracking
- Connection verification before reset operations

## Requirements

### Python Version
- Python 3.7 or higher

### Dependencies
```bash
pip install -r requirements.txt
```

Required packages:
- `pyserial` - Serial communication

## Installation

1. Clone this repository:
```bash
git clone https://github.com/toyo-itorii/Catalyst-Wiper.git
cd Catalyst-Wiper
```

2. Install dependencies:
```bash
pip install pyserial
```

## Usage

### Basic Usage
```bash
python3 main.py
```

## Supported Switch Models

- Cisco Catalyst 2960 Series
- Cisco Catalyst 3560 Series  
- Cisco Catalyst 3750 Series
- Cisco Catalyst 9300 Series
- Cisco Catalyst 9200 Series

*Note: Other IOS-based Catalyst switches may work but are not explicitly tested.*

## What the Script Does

1. **Pre-reset verification**
   - Show a list of used serial ports and ask the user to choose the correct one

2. **Factory reset process**
   - Boot in Rommon mode to perform flash_init
   - Rename flash:config.text flash:config.old
   - Reboot in normal mode
   - Delete the current configuration
   - Delete vlan file

3. **Post-reset verification**
   - Reload again to check if the reset is done
   - Logs completion status

## Safety Features

- **Confirmation prompts** - Requires explicit user confirmation before starting reset process
- **Comprehensive logging** - Detailed operation logs with timestamps
- **Connection testing** - Verifies connectivity before attempting reset

## Output and Logging

Logs are written to:
- Console output (with color coding)

## Troubleshooting

### Common Issues

**Connection timeout**
```
ERROR: Failed to connect to 192.168.1.10: Access Denied
```
- Close every terminal instances of the switch

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/improvement`)
3. Commit your changes (`git commit -am 'Add new feature'`)
4. Push to the branch (`git push origin feature/improvement`)
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Disclaimer

This tool is provided as-is without warranty. Users are responsible for:
- Obtaining proper authorization before use
- Testing in non-production environments
- Maintaining configuration backups
- Understanding the impact of factory reset operations

The authors are not responsible for any damage or data loss resulting from the use of this tool.

## Support

For issues and questions:
- Check the [troubleshooting section](#troubleshooting)
- Review existing [GitHub issues](https://github.com/toyo-itorii/Catalyst-Wiper/issues)
- Create a new issue with detailed error information

## Changelog

### v1.0 (2025-06-23)
- Initial release
- Support for Catalyst 2960/3560/3750 series
- Singe unit processing support

### v1.1 (2025-06-27)
- Seamless automation

### v1.2 (2025-07-04)
- Graphical upgrade
- Log completion status