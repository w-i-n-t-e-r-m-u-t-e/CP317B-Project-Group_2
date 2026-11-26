# CP317B-Project-Group_2
CP317 B Group Project.

**System Security & Update Manager:** a desktop app (Python, PySide6) and a REST API (Java, Spring Boot) that list the devices on a network and flag outdated ones.

## You need
- Java (JDK) 25
- Python 3.10 or newer

## 1. Start the backend
Keep this terminal open. It serves `http://localhost:8080/api/v1/devices`.

macOS / Linux:
```bash
cd cp317-backend
sh mvnw spring-boot:run
```
Windows:
```bat
cd cp317-backend
mvnw.cmd spring-boot:run
```
If Maven picks the wrong Java, set `JAVA_HOME` to your JDK 25 folder.

## 2. Start the app
In a second terminal, from the project folder.

macOS / Linux:
```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python main/main.py
```
Windows:
```bat
py -m venv .venv
.venv\Scripts\pip install -r requirements.txt
.venv\Scripts\python main\main.py
```

## Using it
- **Register device:** add one by hand (name, IPv4 address, version, optional type).
- **Scan network:** pings the 254 addresses around your computer and adds what answers. Some devices ignore pings. Only scan networks you have permission to scan.
- **Latest versions:** enter the newest version for each device type. Devices then show Updated, Outdated or Unknown.

## Agent (reports a computer's OS version)
`agent.py` needs only Python, so you can copy that one file to another computer.
```bash
python3 agent.py                                   # same computer as the backend
python3 agent.py --server http://192.168.1.20:8080  # use the backend computer's IP
```
It reports once each time you run it.

## Checks
```bash
python3 utils/version.py
python3 utils/vendor.py
cd cp317-backend && sh mvnw test
```

## Known limits
- Devices are lost when the backend restarts.
- The API has no login, and anyone on your network can reach it. Do not run it on shared Wi-Fi.
- Latest versions are saved only on the computer running the app.
- The status stored by the backend is always `UPDATED`; the app works out the status it shows.

## Credits
`utils/oui.csv` is the IEEE MA-L list from https://standards-oui.ieee.org/oui/oui.csv, used to name device makers.
