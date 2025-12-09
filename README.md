# Local Share

### What is this?

Basically, I got tired of waiting.

I needed to move 16GB+ files between my laptop and my phone, and everything else sucked. Bluetooth is too slow. Cloud storage (Google Drive, Dropbox) takes forever to upload and then download again. Cables are annoying.

So I built this. It's a "no-nonsense" local file server that runs on your laptop (or phone\!) and lets you blast files across your WiFi at full speed. No internet required. No data caps. No size limits.

### Why use this over Airdrop/Nearby Share?

  * **Size:** I set the limit to 16GB per file. Most apps choke way before that.
  * **Cross-Platform:** It doesn't care if you have an iPhone, Android, Mac, or Windows. It’s just a website. If your device has a browser, it works.
  * **Privacy:** It happens on your local WiFi. Your files never touch the actual internet.

-----

### How to use it (The easy way)

**1. Run the App**
Open your terminal and run the script:

```bash
python main.py
```

**2. Connect**
The terminal will show you an address like `http://192.168.1.5:5000`.
Type that into the browser of any device on the same WiFi.

**3. Authenticate**
Enter the PIN code shown in your terminal (Default: `361022`).

**4. Share**

  * **Files:** Drag and drop huge files. Download them instantly on the other side.
  * **Clipboard:** Copy text on your PC, paste it on your phone (and vice versa).

-----

### Running on Android (Termux)

Yes, you can run the *server* on your phone and download files to your laptop\!

1.  Install **Termux** and **Termux:API** from F-Droid.
2.  Install dependencies: `pkg install python termux-api` and `pip install flask pyperclip`.
3.  Copy this project folder to your phone.
4.  Run `python main.py`.
5.  Turn on your **Hotspot** and connect your laptop to it for blazing fast speeds.

-----

### Tech Stack

  * **Python (Flask):** The heavy lifter backend.
  * **HTML/CSS:** Custom "Terminal/Hacker" style UI because it looks cool.
  * **Pyperclip:** Handles the clipboard syncing magic.

### Future Plans

  * Maybe add a dark mode toggle (even though it's already dark).
  * Add a progress bar for super huge uploads.

-----

**Enjoy the speed.**
