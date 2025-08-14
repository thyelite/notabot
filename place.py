import time, threading, signal, random, sys, ctypes
import mss, cv2, pyautogui, numpy as np
from pynput import keyboard, mouse

# ---------- Windows DPI awareness ----------
if sys.platform.startswith("win"):
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

# ---------- globals ----------
running = False
stop_flag = False
sample_color = None
last_blob_rect = None  # (x1, y1, x2, y2)

# ---------- keyboard handling ----------
def on_press(key):
    global running, stop_flag
    try:
        if key == keyboard.Key.enter:
            running = not running
            print(("▶️  START" if running else "⏸️  PAUSE"))
        elif key == keyboard.Key.esc:
            stop_flag = True
    except Exception:
        pass

def kb_listener_thread():
    with keyboard.Listener(on_press=on_press) as listener:
        listener.join()

def handle_sigint(signum, frame):
    global stop_flag
    stop_flag = True
signal.signal(signal.SIGINT, handle_sigint)

# ---------- color sampling ----------
def get_pixel_color(x, y):
    img = pyautogui.screenshot(region=(x, y, 1, 1))
    return img.getpixel((0, 0))

def prompt_color_pick():
    print("Click anywhere on the screen to sample the target color...")
    def on_click(x, y, button, pressed):
        global sample_color
        if pressed:
            sample_color = get_pixel_color(x, y)
            print(f"Sampled color RGB: {sample_color}")
            return False  # stop listener
    with mouse.Listener(on_click=on_click) as listener:
        listener.join()

# ---------- main loop ----------
def main():
    global stop_flag, sample_color, last_blob_rect
    prompt_color_pick()

    tol_in = input("Enter tolerance (default 15): ").strip()
    tol = int(tol_in) if tol_in.isdigit() else 15

    pyautogui.FAILSAFE = True
    threading.Thread(target=kb_listener_thread, daemon=True).start()

    with mss.mss() as sct:
        mon = sct.monitors[0]
        print(f"Ready. Color={sample_color} tol={tol}. Press ENTER to start/stop, ESC or Ctrl+C to quit.")
        print("⏸️  Waiting for ENTER to begin...")

        while not stop_flag:
            shot = sct.grab(mon)
            frame = np.array(shot)[:, :, :3]  # BGR
            bgr = (sample_color[2], sample_color[1], sample_color[0])

            lower = np.array([max(0, bgr[0]-tol), max(0, bgr[1]-tol), max(0, bgr[2]-tol)], dtype=np.uint8)
            upper = np.array([min(255, bgr[0]+tol), min(255, bgr[1]+tol), min(255, bgr[2]+tol)], dtype=np.uint8)
            mask = cv2.inRange(frame, lower, upper)

            # Live preview (non-blocking)
            cv2.imshow("mask preview (ESC to quit)", mask)
            cv2.waitKey(1)  # doesn't block, just updates window

            if running:
                num, labels, stats, centroids = cv2.connectedComponentsWithStats(mask, connectivity=4)
                for i in range(1, num):
                    if stop_flag: break  # quick exit check
                    x, y, w, h, area = stats[i]
                    if w >= 2 and h >= 2:
                        cx, cy = map(int, centroids[i])

                        # Check if current mouse position is inside the blob
                        mx, my = pyautogui.position()
                        blob_rect = (x, y, x + w, y + h)
                        inside_blob = blob_rect[0] <= mx <= blob_rect[2] and blob_rect[1] <= my <= blob_rect[3]

                        if inside_blob and last_blob_rect == blob_rect:
                            continue  # skip same blob

                        pyautogui.moveTo(cx, cy, duration=0)
                        pyautogui.click()
                        last_blob_rect = blob_rect
                        time.sleep(random.uniform(0.045, 0.08))  # 4× faster clicks

    cv2.destroyAllWindows()
    print("Exiting. Bye!")

if __name__ == "__main__":
    main()
