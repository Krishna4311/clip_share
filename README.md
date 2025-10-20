# CLIP SHARE 
# Local Network Clipboard and File Sharer

A simple, self-contained Python application for sharing your clipboard and files between devices on the same local Wi-Fi network. No cloud services, no complex setup-just a single script that runs a lightweight web server on your host machine.

Gemini: \[███████---| 70%\]

## Features

- **Real-Time Clipboard Sync:** Text copied or sent from any connected device is automatically updated on all others.
- **Multi-File Sharing:** Easily upload multiple files (photos, videos, documents) from your phone or computer.
- **Flexible Downloads:** Download shared files individually or all at once as a convenient ZIP archive.
- **Ephemeral Storage:** All uploaded files are stored temporarily and are automatically deleted when you close the application.
- **Private and Secure:** Operates entirely within your local network. No data ever leaves your Wi-Fi.
- **Cross-Platform:** Works on Windows, macOS, and Linux.

## How It Works

The application runs a local web server (using Flask) on a "host" computer. Any other device on the same Wi-Fi network (laptops, phones, tablets) can connect to this host by simply opening a web browser and navigating to the host's local IP address. The web page acts as a central hub for all sharing activities.

## Setup and Usage

### Prerequisites

- **Python 3.x** installed on the host machine.

### 1\. Installation

Open your terminal or command prompt and install the necessary Python packages:
```
pip install Flask pyperclip  
```
### 2\. Running the Application

- Save the code as clip_share.py.
- Navigate to the file's directory in your terminal.
- Run the script:  
    python clip_share.py  

- The terminal will display the local IP address where the server is running. It will look something like this:
```
    \--- Local Sharer ---  
    Server is running. Open your browser and go to:  
    \http://192.168.1.10:5000
    \---------------------------------  
    Press CTRL+C to stop the server.  
```
### 3\. Connecting from Other Devices

- Ensure your other devices (e.g., your phone) are connected to the **same Wi-Fi network** as the host computer.
- Open the web browser on your device.
- Type the http://... address from the terminal into the browser's address bar.
- You can now share your clipboard and files!

## Creating a Standalone Executable (Optional)

You can package this script into a single .exe (Windows) or .app (macOS) file so you don't need to run it from the terminal every time.

### 1\. Install PyInstaller
```
pip install pyinstaller  
```
### 2\. Package the Script

Navigate to the script's directory and run the following command:
```
pyinstaller --onefile clip_share.py  
```
### 3\. Run the App

Once finished, you will find a dist folder. Inside, your standalone application (clip_share.exe or clip_share.app) is ready to be used. Just double-click it to start the server. The uploads folder will be created right next to it. To stop the server, simply close the terminal window that appears.
