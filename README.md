# Sequential Multi-Color Blob Clicker

This Python script finds and clicks on-screen blobs matching a sequence of colors you define, **one color at a time**, waiting for you to press `ENTER` to advance to the next color.

---

## Features
- **Sequential color workflow** – Clicks blobs for Color #1, pauses, then waits for you to press `ENTER` before moving on to Color #2, and so on.
- **Exact color picking** – Click directly on the screen to sample each color.
- **Fast, human-like clicking** – Random delay between clicks (0.045–0.08s).
- **Quit anytime** – Press `ESC` or move cursor to the top left corner of your screen (failsafe)

---

## Requirements
- **Python 3.8+**
- Libraries:
  ```bash
  pip install mss opencv-python numpy pyautogui pynput keyboard

  
## Usage

1. Run the script as administrator:
   ```bash
   python place.py
   ```
2. Enter the number of colors you want to track.
3. For each color:
   - When prompted, click directly on the screen to sample that color.
4. The script starts **paused** at the first color.
5. Press `ENTER` to click **all blobs** matching the current color (≥ 2×2 px, 4-connectivity).
6. After finishing that color, the script **auto-pauses** and advances to the next color.
7. Repeat until all colors are processed.
8. Quit at any time with `ESC` or `Ctrl+C`.

---

## Notes

- **Tolerance:** Fixed at `15`. Adjust in code (`tol = 15`) if you need looser/tighter matching.
- **Connectivity:** Uses 4-connectivity (diagonals are not connected).
- **Blob filter:** Ignores blobs smaller than `2×2` pixels.
- **Global hotkeys:**  
  - Requires the `keyboard` library and running the script **as Administrator** on Windows for `ENTER`/`ESC` to work outside the Python window.  
    ```bash
    pip install keyboard
    ```
  - Without it, `ENTER`/`ESC` only work when the console or the preview window has focus.
- **Preview:** The mask preview window (if present in your version) shows matched pixels in white and background in black for verification.
