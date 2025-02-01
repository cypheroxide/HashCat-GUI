# HashCat-GUI

A modern, Linux-native GUI for Hashcat that provides an intuitive interface for hash cracking operations. This application combines the power of Hashcat's command-line functionality with a user-friendly web interface, making it easier to manage and monitor hash cracking tasks.

## Features

- Modern, responsive web-based GUI interface
- Real-time progress monitoring
- Support for multiple hash types and attack modes
- Session management and restore capabilities
- Wordlist and rules management
- Hardware acceleration support (CPU, GPU)
- Task queue management
- Results export functionality

## Dependencies

- Python 3.8 or higher
- hashcat
- Node.js and npm (for frontend development)
- Web browser (Firefox, Chrome, or compatible)

Additional Python dependencies are listed in `requirements.txt`.

## Installation

### Debian/Ubuntu-based Systems

```bash
# Install system dependencies
sudo apt update
sudo apt install -y python3 python3-pip hashcat

# Install HashCat-GUI
git clone https://github.com/cypheroxide/HashCat-GUI.git
cd HashCat-GUI
sudo ./install.sh
```

### Arch Linux / BlackArch

```bash
# Using AUR helper (yay)
yay -S hashcat-gui

# Manual installation from source
git clone https://github.com/cypheroxide/HashCat-GUI.git
cd HashCat-GUI
makepkg -si
```

## Usage

1. Start the HashCat-GUI service:
```bash
systemctl --user start hashcat-gui
```

2. Open your web browser and navigate to `http://localhost:8080`

3. Start a new cracking session:
- Select hash type
- Choose attack mode
- Configure additional options
- Upload wordlists or rules if needed
- Start the session

4. Monitor progress and results in real-time through the web interface

## Security Considerations

- HashCat-GUI runs with user privileges and should not be executed as root
- The web interface is accessible only from localhost by default
- Ensure proper file permissions for wordlists and hash files
- Keep hashcat and HashCat-GUI updated to the latest versions
- Be cautious when using custom wordlists from untrusted sources
- Review and understand the implications of different attack modes before use

## License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.

## Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details on how to submit pull requests, report issues, and contribute to the project.

For security-related matters, please review our [Security Policy](SECURITY.md).
