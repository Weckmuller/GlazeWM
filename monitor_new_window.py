import sys, json, ctypes, subprocess, logging
from ctypes import wintypes

# Initialize logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s: %(message)s')

def get_mouse_workspace():
    # Get current mouse position (same as in monitor_workspace_switch/transfer)
    user32 = ctypes.windll.user32
    pt = wintypes.POINT()
    user32.GetCursorPos(ctypes.byref(pt))
    cursor = (pt.x, pt.y)
    logging.debug(f"Cursor position: {cursor}")
    
    # Enumerate monitors.
    class RECT(ctypes.Structure):
        _fields_ = [("left", ctypes.c_long), ("top", ctypes.c_long),
                    ("right", ctypes.c_long), ("bottom", ctypes.c_long)]
    monitors = []
    def callback(hMonitor, hdcMonitor, lprcMonitor, dwData):
        r = ctypes.cast(lprcMonitor, ctypes.POINTER(RECT)).contents
        monitors.append((hMonitor, (r.left, r.top, r.right, r.bottom)))
        return 1
    MonitorEnumProc = ctypes.WINFUNCTYPE(ctypes.c_int, ctypes.c_ulong, ctypes.c_ulong, ctypes.POINTER(RECT), ctypes.c_double)
    user32.EnumDisplayMonitors(0, 0, MonitorEnumProc(callback), 0)
    logging.debug(f"Found {len(monitors)} monitor(s)")
    
    # Determine the monitor index containing the cursor.
    current_monitor_index = 0
    for idx, mon in enumerate(monitors):
        left, top, right, bottom = mon[1]
        logging.debug(f"Monitor {idx} bounds: {(left, top, right, bottom)}")
        if left <= cursor[0] < right and top <= cursor[1] < bottom:
            current_monitor_index = idx
            break
    logging.debug(f"Current monitor index: {current_monitor_index}")
    
    # Query current workspaces from glazewm.
    try:
        result = subprocess.check_output("glazewm query workspaces", shell=True, text=True)
        data = json.loads(result)
        workspaces = data.get("data", {}).get("workspaces", [])
    except Exception as e:
        logging.error(f"Workspace query error: {e}")
        workspaces = []
    
    # Filter workspaces by bind_to_monitor matching current_monitor_index (handle type conversion).
    candidates = [ws for ws in workspaces if ws.get("bind_to_monitor") is not None 
                  and int(ws.get("bind_to_monitor")) == current_monitor_index]
    if candidates:
        focused = next((ws for ws in candidates if ws.get("hasFocus")), None)
        workspace = focused.get("name") if focused else candidates[0].get("name")
    else:
        # Fallback mapping: assign "a1" for monitor 0, "b1" for monitor 1.
        workspace = "a1" if current_monitor_index == 0 else "b1"
    logging.debug(f"Selected workspace: {workspace}")
    return workspace

def move_window_to_workspace(window_id, workspace):
    # Removed "--id {window_id}" since glazewm command move operates on focused window.
    command = f"glazewm command move --workspace {workspace}"
    logging.debug(f"Executing command: {command}")
    si = subprocess.STARTUPINFO()
    si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    si.wShowWindow = subprocess.SW_HIDE
    result = subprocess.run(command, shell=True, startupinfo=si, capture_output=True, text=True)
    logging.debug(f"Command result: returncode={result.returncode}, stdout={result.stdout}, stderr={result.stderr}")

def main():
    # Subscribe to all events.
    subproc = subprocess.Popen(["glazewm", "sub", "-e", "all"], stdout=subprocess.PIPE, text=True)
    logging.debug("Subscribed to glazewm events")
    while True:
        line = subproc.stdout.readline()
        if not line:
            continue
        logging.debug(f"Event line: {line.strip()}")
        try:
            event = json.loads(line.strip())
        except Exception as e:
            logging.error(f"JSON parse error: {e}")
            continue
        # Check for window_managed events.
        data = event.get("data", {})
        if data.get("eventType") == "window_managed":
            managed = data.get("managedWindow", {})
            window_id = managed.get("id")
            logging.debug(f"New window managed with id: {window_id}")
            if window_id:
                # Determine target workspace based on mouse position.
                workspace = get_mouse_workspace()
                if workspace:
                    move_window_to_workspace(window_id, workspace)
                else:
                    logging.error("Unable to determine target workspace")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
