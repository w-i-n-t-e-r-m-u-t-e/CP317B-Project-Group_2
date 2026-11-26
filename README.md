# CP317B-Project-Group_2
CP317 B Group Project.

**System Security & Update Manager:** a desktop app (Python, PySide6) and a REST API (Java, Spring Boot) that list the devices on a network and flag outdated ones.

## You need
- Java (JDK) 25
- Python 3.10 or newer

## Set up once
macOS / Linux:
```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```
Windows:
```bat
py -m venv .venv
.venv\Scripts\pip install -r requirements.txt
```

## Run
One command starts the backend and the app, and stops the backend when you close the window.
```bash
.venv/bin/python run.py
```
Windows: `.venv\Scripts\python run.py`. If it cannot find Java, set `JAVA_HOME` to your JDK 25 folder. Errors are in `backend.log`.

## Using it
- The app opens on what needs your attention: new devices ("Is this yours?"), ones you don't recognise, and your outdated ones. **Show all devices** has the full table.
- **Register device:** add one by hand (name, IPv4 or IPv6 address, version, optional type).
- **Scan network:** pings the 254 addresses around your computer and adds what answers. Some devices ignore pings. Only scan networks you have permission to scan.
- **IPv6-only networks** (some phone hotspots): the scan sends one ping to all neighbours instead of trying each address. It works on macOS and Linux, and misses devices that ignore the ping.
- **Update status:** macOS, iOS, Windows, Ubuntu and Android are checked against [endoflife.date](https://endoflife.date) (needs internet; only the product name is sent). Windows, Ubuntu and Android can only be shown as supported or not. **Latest versions** overrides this by hand.
- **This computer:** each scan fills in its type and version automatically and marks it **Mine**.
- **Safety check:** each scan looks for Telnet, FTP, screen sharing and video streams on devices you marked **Mine**. Finding nothing does not prove a device is safe.
- **Rescan every 15 min:** off until you tick it.

## Checks
```bash
python3 utils/version.py
python3 utils/vendor.py
python3 utils/scan6.py
python3 utils/attention.py
python3 -m utils.releases
python3 -m utils.ports
cd cp317-backend && sh mvnw test
```

## Known limits
- Devices are saved in `cp317-backend/data/`. Delete that folder to start fresh.
- The API has no login, and anyone on your network can reach it. Do not run it on shared Wi-Fi.
- Latest versions are saved only on the computer running the app.
- The status stored by the backend is always `UPDATED`; the app works out the status it shows.

## Credits
`utils/oui.csv` is the IEEE MA-L list from https://standards-oui.ieee.org/oui/oui.csv, used to name device makers.
