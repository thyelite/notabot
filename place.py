import time, signal, random, sys, ctypes
import mss, cv2, pyautogui, numpy as np

# ---------- Windows DPI awareness ----------
if sys.platform.startswith("win"):
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

# ---------- config ----------
TOL = 15
CLICK_DELAY_RANGE = (0.045, 0.08)
NO_MATCH_FRAMES_TO_FINISH = 30  # ~1/2 to 1 sec depending on your loop speed

# ---------- helpers ----------
def parse_hex(hexstr):
    s = hexstr.strip().lstrip('#')
    if len(s) != 6 or any(c not in "0123456789abcdefABCDEF" for c in s):
        raise ValueError(f"Bad hex color: {hexstr}")
    return (int(s[0:2],16), int(s[2:4],16), int(s[4:6],16))  # RGB

def bgr_bounds_from_rgb(rgb, tol=TOL):
    bgr = (rgb[2], rgb[1], rgb[0])
    lower = np.array([max(0, bgr[0]-tol), max(0, bgr[1]-tol), max(0, bgr[2]-tol)], dtype=np.uint8)
    upper = np.array([min(255, bgr[0]+tol), min(255, bgr[1]+tol), min(255, bgr[2]+tol)], dtype=np.uint8)
    return lower, upper

def centroid_in_any_rect(cx, cy, rects, pad=3):
    for (x1,y1,x2,y2) in rects:
        if x1-pad <= cx <= x2+pad and y1-pad <= cy <= y2+pad:
            return True
    return False

stop_flag = False
def handle_sigint(signum, frame):
    global stop_flag
    stop_flag = True
signal.signal(signal.SIGINT, handle_sigint)

def main():
    global stop_flag
    # --- collect colors ---
    while True:
        try:
            n = int(input("How many colors? ").strip())
            if n <= 0: raise ValueError
            break
        except Exception:
            print("Enter a positive integer.")
    colors_rgb = []
    for i in range(n):
        while True:
            try:
                hx = input(f"HEX color #{i+1} (e.g. #1e90ff): ").strip()
                colors_rgb.append(parse_hex(hx))
                break
            except Exception as e:
                print(e)

    pyautogui.FAILSAFE = True
    clicked_rects = []  # remember all blobs ever clicked (across all colors)

    with mss.mss() as sct:
        mon = sct.monitors[0]
        print(f"\nLoaded colors: {colors_rgb}  tol={TOL}")
        print("Press ENTER in this console to start each color; ESC in preview or Ctrl+C exits.\n")

        # process colors sequentially
        for idx, rgb in enumerate(colors_rgb, 1):
            if stop_flag: break

            input(f"[{idx}/{len(colors_rgb)}] Ready for color {rgb}. Press ENTER to start...")

            lower, upper = bgr_bounds_from_rgb(rgb)
            no_match_frames = 0
            print(f"→ Working color {rgb}. (ESC/Ctrl+C to quit this run)")

            while not stop_flag:
                shot = sct.grab(mon)
                frame = np.array(shot)[:, :, :3]  # BGR

                mask = cv2.inRange(frame, lower, upper)
                cv2.imshow("mask preview (ESC to quit)", mask)
                k = cv2.waitKey(1) & 0xFF
                if k == 27:  # ESC in the preview
                    stop_flag = True
                    break

                num, labels, stats, cents = cv2.connectedComponentsWithStats(mask, connectivity=4)

                # collect eligible blobs
                eligible = []
                for i in range(1, num):
                    x, y, w, h, area = stats[i]
                    if w >= 2 and h >= 2:
                        cx, cy = map(int, cents[i])
                        # skip if this blob (by centroid) was ever clicked before
                        if centroid_in_any_rect(cx, cy, clicked_rects):
                            continue
                        eligible.append((x, y, w, h, cx, cy))

                if not eligible:
                    no_match_frames += 1
                else:
                    no_match_frames = 0

                # if no matches for a while, auto-finish this color
                if no_match_frames >= NO_MATCH_FRAMES_TO_FINISH:
                    print(f"✓ Finished color {rgb} (no matches recently).")
                    break

                # click all current eligible blobs (fast, one pass)
                for x, y, w, h, cx, cy in eligible:
                    if stop_flag: break
                    pyautogui.moveTo(cx, cy, duration=0)
                    pyautogui.click()
                    clicked_rects.append((x, y, x + w, y + h))
                    if len(clicked_rects) > 2000:
                        clicked_rects = clicked_rects[-1000:]
                    time.sleep(random.uniform(*CLICK_DELAY_RANGE))

        cv2.destroyAllWindows()
        print("Done.")

if __name__ == "__main__":
    main()
