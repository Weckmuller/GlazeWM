import sys, ctypes, subprocess, json
from ctypes import wintypes

if len(sys.argv) < 2 or sys.argv[1] not in ['next', 'prev']:
    sys.exit(1)
direction = sys.argv[1]

# Get current mouse position
user32 = ctypes.windll.user32
pt = wintypes.POINT()
user32.GetCursorPos(ctypes.byref(pt))
cursor = (pt.x, pt.y)

# Enumerate monitors and their bounds
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

# Determine monitor index containing the mouse (default to 0)
current_monitor_index = 0
for idx, mon in enumerate(monitors):
    left, top, right, bottom = mon[1]
    if left <= cursor[0] < right and top <= cursor[1] < bottom:
        current_monitor_index = idx
        break
prefix = 'a' if current_monitor_index == 0 else 'b' if current_monitor_index == 1 else 'a'

# Query workspaces from glazewm and parse JSON
try:
    result = subprocess.check_output("glazewm query workspaces", shell=True, text=True)
    data = json.loads(result)
    workspaces = data.get("data", {}).get("workspaces", [])
except Exception:
    sys.exit(1)

# Filter workspaces with matching prefix and extract numeric order
filtered = []
for ws in workspaces:
    name = ws.get("name", "")
    try:
        num = int(''.join(filter(str.isdigit, name)))
    except ValueError:
        continue
    if name.startswith(prefix):
        filtered.append((num, name, ws.get("hasFocus", False)))
if not filtered:
    sys.exit(1)
filtered.sort(key=lambda x: x[0])

# Find current focused workspace from filtered list, default to first if none
current_idx = next((i for i, (_, _, hf) in enumerate(filtered) if hf), 0)

# Calculate new index with wrap-around and update the workspace focus
if direction == 'next':
    target_idx = (current_idx + 1) % len(filtered)
else:
    target_idx = (current_idx - 1) % len(filtered)
target_workspace = filtered[target_idx][1]

command = f"glazewm command focus --workspace {target_workspace}"
si = subprocess.STARTUPINFO()
si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
si.wShowWindow = subprocess.SW_HIDE
subprocess.run(command, shell=True, startupinfo=si, capture_output=True, text=True)
