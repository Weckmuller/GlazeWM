import sys, ctypes, subprocess
from ctypes import wintypes

# Get the current mouse position
user32 = ctypes.windll.user32
pt = wintypes.POINT()
user32.GetCursorPos(ctypes.byref(pt))
cursor = (pt.x, pt.y)

# Enumerate monitors and their bounds
class RECT(ctypes.Structure):
    _fields_ = [("left", ctypes.c_long), ("top", ctypes.c_long),
                ("right", ctypes.c_long), ("bottom", ctypes.c_long)]

monitors = []  # List of tuples: (handle, (left, top, right, bottom))
def callback(hMonitor, hdcMonitor, lprcMonitor, dwData):
    r = ctypes.cast(lprcMonitor, ctypes.POINTER(RECT)).contents
    monitors.append((hMonitor, (r.left, r.top, r.right, r.bottom)))
    return 1

MonitorEnumProc = ctypes.WINFUNCTYPE(ctypes.c_int, ctypes.c_ulong, ctypes.c_ulong, ctypes.POINTER(RECT), ctypes.c_double)
user32.EnumDisplayMonitors(0, 0, MonitorEnumProc(callback), 0)

# Determine monitor index containing the mouse (default to first)
current_monitor_index = 0
for idx, mon in enumerate(monitors):
    left, top, right, bottom = mon[1]
    if left <= cursor[0] < right and top <= cursor[1] < bottom:
        current_monitor_index = idx
        break

# Map key press to workspace per monitor. Keys '1'-'9' and '0' are accepted.
if current_monitor_index == 0:
    mapping = {
        '1': 'a1', '2': 'a2', '3': 'a3', '4': 'a4', '5': 'a5',
        '6': 'a6', '7': 'a7', '8': 'a8', '9': 'a9', '0': 'a10'
    }
elif current_monitor_index == 1:
    mapping = {
        '1': 'b1', '2': 'b2', '3': 'b3', '4': 'b4', '5': 'b5',
        '6': 'b6', '7': 'b7', '8': 'b8', '9': 'b9', '0': 'b10'
    }
else:
    mapping = {
        '1': 'a1', '2': 'a2', '3': 'a3', '4': 'a4', '5': 'a5',
        '6': 'a6', '7': 'a7', '8': 'a8', '9': 'a9', '0': 'a10'
    }

if len(sys.argv) < 2 or sys.argv[1] not in mapping:
    sys.exit(1)

target_workspace = mapping[sys.argv[1]]
command = f"glazewm command focus --workspace {target_workspace}"
si = subprocess.STARTUPINFO()
si.dwFlags |= subprocess.STARTF_USESHOWWINDOW  # use startupinfo to hide window
si.wShowWindow = subprocess.SW_HIDE
result = subprocess.run(
    command,
    shell=True,
    startupinfo=si,
    capture_output=True,
    text=True
)
