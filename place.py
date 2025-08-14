import time, signal, random, sys, ctypes
import mss, cv2, pyautogui, numpy as np
from pynput import mouse
try:
    import keyboard  # global key polling
    HAS_KBD = True
except Exception:
    HAS_KBD = False

# ---- Windows DPI awareness ----
if sys.platform.startswith("win"):
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

stop_flag = False
pyautogui.FAILSAFE = True

def handle_sigint(signum, frame):
    global stop_flag
    stop_flag = True
signal.signal(signal.SIGINT, handle_sigint)

# ---------- color picking ----------
def get_pixel_color(x, y):
    img = pyautogui.screenshot(region=(x, y, 1, 1))
    return img.getpixel((0, 0))  # (R,G,B)

def pick_one_color(idx):
    print(f"Click color #{idx} on screen...")
    picked = [None]
    def on_click(x, y, button, pressed):
        if pressed:
            picked[0] = get_pixel_color(x, y)
            print(f"  → sampled RGB {picked[0]}")
            return False
    with mouse.Listener(on_click=on_click) as L:
        L.join()
    return picked[0]

def pick_colors():
    try:
        n = int(input("How many colors to track? (default 1): ").strip() or "1")
    except:
        n = 1
    colors = []
    for i in range(1, n + 1):
        colors.append(pick_one_color(i))
    return colors

# ---------- helpers ----------
def rgb_to_hex(rgb):
    return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"

def build_mask_for_color(frame_bgr, rgb, tol):
    bgr = (rgb[2], rgb[1], rgb[0])
    lower = np.array([max(0, bgr[0] - tol), max(0, bgr[1] - tol), max(0, bgr[2] - tol)], dtype=np.uint8)
    upper = np.array([min(255, bgr[0] + tol), min(255, bgr[1] + tol), min(255, bgr[2] + tol)], dtype=np.uint8)
    return cv2.inRange(frame_bgr, lower, upper)

def map_coords(cx, cy, shot_mon, frame_w, frame_h):
    left, top, width, height = shot_mon["left"], shot_mon["top"], shot_mon["width"], shot_mon["height"]
    sx = int(cx * (width / frame_w)) + left
    sy = int(cy * (height / frame_h)) + top
    return sx, sy

# ---------- main ----------
def main():
    global stop_flag
    colors = pick_colors()
    tol = 15  # fixed tolerance

    if not HAS_KBD:
        print("WARNING: `keyboard` not installed. ENTER will only work when the preview window is focused.")
        print("Install for global ENTER:  pip install keyboard  (run script as Administrator on Windows)")

    enter_down = False
    esc_down = False

    with mss.mss() as sct:
        mon = sct.monitors[0]
        print(f"\nColors: {[rgb_to_hex(c) for c in colors]}  tol={tol}")
        print("Flow: ENTER → click ALL blobs for current color → auto-pause → ENTER for next color…")
        print("Quit: ESC or Ctrl+C")
        current = 0
        print(f"\nPaused at color #{current+1}: {rgb_to_hex(colors[current])}. Press ENTER to run this color.")

        while not stop_flag and current < len(colors):
            key = cv2.waitKey(1) & 0xFF
            if HAS_KBD:
                if keyboard.is_pressed('esc'):
                    if not esc_down:
                        stop_flag = True
                    esc_down = True
                else:
                    esc_down = False
                if keyboard.is_pressed('enter') or keyboard.is_pressed('return'):
                    if not enter_down:
                        print(f"Processing color #{current+1}: {rgb_to_hex(colors[current])}")
                        clicks = process_one_color(sct, mon, colors[current], tol)
                        print(f"Done color #{current+1}: clicked {clicks} blob(s).")
                        current += 1
                        if current < len(colors):
                            print(f"Paused at color #{current+1}: {rgb_to_hex(colors[current])}. Press ENTER.")
                        continue
                    enter_down = True
                else:
                    enter_down = False
            else:
                if key in (13, 10):  # Enter/Return
                    print(f"Processing color #{current+1}: {rgb_to_hex(colors[current])}")
                    clicks = process_one_color(sct, mon, colors[current], tol)
                    print(f"Done color #{current+1}: clicked {clicks} blob(s).")
                    current += 1
                    if current < len(colors):
                        print(f"Paused at color #{current+1}: {rgb_to_hex(colors[current])}. Press ENTER.")
                if key == 27:  # ESC
                    stop_flag = True

        print("Finished all colors." if not stop_flag else "Stopping…")

def process_one_color(sct, mon, rgb, tol):
    shot = sct.grab(mon)
    frame = np.array(shot)[:, :, :3]  # BGR
    fh, fw = frame.shape[:2]
    mask = build_mask_for_color(frame, rgb, tol)
    num, labels, stats, cents = cv2.connectedComponentsWithStats(mask, connectivity=4)
    clicks = 0
    for i in range(1, num):
        x, y, w, h, area = stats[i]
        if w >= 2 and h >= 2:
            cx, cy = map(int, cents[i])
            sx, sy = map_coords(cx, cy, mon, fw, fh)
            try:
                pyautogui.moveTo(sx, sy, duration=0)
                pyautogui.click()
                clicks += 1
                time.sleep(random.uniform(0.045, 0.08))
            except Exception as e:
                print(f"Click error at ({sx},{sy}): {e}")
    return clicks

if __name__ == "__main__":
    main()
