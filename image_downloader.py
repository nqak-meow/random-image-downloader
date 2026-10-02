import json
import os
import queue
import threading
import time
import tkinter as tk
import urllib.error
import urllib.request
from tkinter import filedialog, messagebox, ttk

try:
    from PIL import Image, ImageTk
except ImportError:
    Image = None
    ImageTk = None

OUT_DIR = os.path.join(os.path.expanduser("~"), "Downloads", "random_images")
HISTORY_FILE = os.path.join(os.path.expanduser("~"), "Downloads",
                            "random_images_history.json")
BASE_URL = "https://picsum.photos"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) ImageAutoDownloader/1.0"
SIZES = (("640x480", 640, 480), ("800x600", 800, 600), ("1024x768", 1024, 768),
         ("1200x800", 1200, 800), ("1600x900", 1600, 900), ("1920x1080", 1920, 1080))

BG = "#1e1e28"
FG = "#e6e6f0"
ACCENT = "#3d7eff"
MUTED = "#8a8aa0"


class DownloaderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Random Image Auto Downloader")
        self.root.geometry("860x660")
        self.root.configure(bg=BG)

        self.stop_event = threading.Event()
        self.thread = None
        self.events = queue.Queue()
        self.preview_photo = None
        self.saved = 0
        self.last_outdir = OUT_DIR

        self.outdir_var = tk.StringVar(value=OUT_DIR)
        self.interval_var = tk.StringVar(value="3")
        self.count_var = tk.StringVar(value="20")
        self.size_var = tk.StringVar(value="1024x768")
        self.gray_var = tk.BooleanVar(value=False)
        self.blur_var = tk.IntVar(value=0)
        self.preview_var = tk.BooleanVar(value=Image is not None)

        self._build_ui()

        self.root.after(100, self._poll_events)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self):
        top = tk.Frame(self.root, bg=BG)
        top.pack(fill="x", padx=14, pady=(14, 6))

        tk.Label(top, text="Random Image Auto Downloader", font=("Arial", 16, "bold"),
                 bg=BG, fg=FG).pack(side="left")
        tk.Label(top, text="source: picsum.photos", font=("Arial", 10),
                 bg=BG, fg=MUTED).pack(side="left", padx=(24, 0))

        body = tk.Frame(self.root, bg=BG)
        body.pack(fill="both", expand=True, padx=14, pady=6)

        opts = tk.Frame(body, bg=BG)
        opts.pack(side="left", fill="y")

        tk.Label(opts, text="Size:", font=("Arial", 10), bg=BG, fg=MUTED).pack(anchor="w")
        ttk.Combobox(opts, textvariable=self.size_var, width=12,
                     values=[s[0] for s in SIZES], state="readonly",
                     font=("Arial", 10)).pack(anchor="w", pady=(2, 10))

        tk.Label(opts, text="Count (0 = infinite):", font=("Arial", 10), bg=BG,
                 fg=MUTED).pack(anchor="w")
        tk.Entry(opts, textvariable=self.count_var, font=("Arial", 10), width=12,
                 bg="#141420", fg=FG, insertbackground=FG, relief="flat",
                 highlightthickness=0).pack(anchor="w", pady=(2, 10))

        tk.Label(opts, text="Interval (sec):", font=("Arial", 10), bg=BG,
                 fg=MUTED).pack(anchor="w")
        tk.Entry(opts, textvariable=self.interval_var, font=("Arial", 10), width=12,
                 bg="#141420", fg=FG, insertbackground=FG, relief="flat",
                 highlightthickness=0).pack(anchor="w", pady=(2, 10))

        tk.Label(opts, text="Blur (0-10):", font=("Arial", 10), bg=BG,
                 fg=MUTED).pack(anchor="w")
        tk.Scale(opts, from_=0, to=10, orient="horizontal", variable=self.blur_var,
                 bg=BG, fg=MUTED, troughcolor="#141420", activebackground=ACCENT,
                 highlightthickness=0, bd=0, sliderrelief="flat").pack(
                     anchor="w", pady=(2, 10))

        tk.Checkbutton(opts, text="Grayscale", variable=self.gray_var, bg=BG, fg=FG,
                       selectcolor=BG, activebackground=BG, activeforeground=FG,
                       font=("Arial", 10)).pack(anchor="w")
        if Image is not None:
            tk.Checkbutton(opts, text="Show preview", variable=self.preview_var, bg=BG,
                           fg=FG, selectcolor=BG, activebackground=BG,
                           activeforeground=FG, font=("Arial", 10)).pack(anchor="w")
        else:
            tk.Label(opts, text="preview off (pip install pillow)", font=("Arial", 8),
                     bg=BG, fg=MUTED).pack(anchor="w")

        right = tk.Frame(body, bg=BG)
        right.pack(side="left", fill="both", expand=True, padx=(16, 0))

        self.preview = tk.Label(right, text="No preview", bg="#141420", fg=MUTED,
                                font=("Arial", 11), height=12, width=42)
        self.preview.pack(fill="both", expand=True)

        log_frame = tk.LabelFrame(right, text="Log", bg=BG, fg=MUTED,
                                  font=("Arial", 9), relief="flat")
        log_frame.pack(fill="both", expand=False, pady=(10, 0))
        self.log_box = tk.Text(log_frame, font=("Consolas", 9), bg="#141420", fg=FG,
                               relief="flat", height=7, wrap="none", state="disabled")
        log_sb = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_box.yview)
        self.log_box.configure(yscrollcommand=log_sb.set)
        self.log_box.pack(side="left", fill="both", expand=True)
        log_sb.pack(side="right", fill="y")

        dest = tk.Frame(self.root, bg=BG)
        dest.pack(fill="x", padx=14, pady=(6, 0))

        tk.Label(dest, text="Save to:", font=("Arial", 10), bg=BG, fg=MUTED).pack(side="left")
        tk.Entry(dest, textvariable=self.outdir_var, font=("Arial", 10), bg="#141420",
                 fg=FG, insertbackground=FG, relief="flat").pack(side="left",
                                                                  fill="x", expand=True,
                                                                  padx=8, ipady=4)
        tk.Button(dest, text="Browse", command=self._browse, bg="#2c2c3c", fg=FG,
                  activebackground="#3a3a4e", relief="flat", font=("Arial", 10),
                  padx=12).pack(side="right")

        actions = tk.Frame(self.root, bg=BG)
        actions.pack(fill="x", padx=14, pady=10)

        self.start_btn = tk.Button(actions, text="Start", command=self.start,
                                   bg=ACCENT, fg="#ffffff", activebackground="#5590ff",
                                   relief="flat", font=("Arial", 11, "bold"),
                                   padx=26, pady=7)
        self.start_btn.pack(side="left")

        self.stop_btn = tk.Button(actions, text="Stop", command=self.stop, state="disabled",
                                  bg="#2c2c3c", fg=FG, activebackground="#3a3a4e",
                                  relief="flat", font=("Arial", 11), padx=20, pady=7)
        self.stop_btn.pack(side="left", padx=10)

        tk.Button(actions, text="One image", command=self.start_single, bg="#2c2c3c",
                  fg=FG, activebackground="#3a3a4e", relief="flat",
                  font=("Arial", 11), padx=16, pady=7).pack(side="left")

        tk.Button(actions, text="Open folder", command=self._open_folder, bg="#2c2c3c",
                  fg=FG, activebackground="#3a3a4e", relief="flat", font=("Arial", 11),
                  padx=16, pady=7).pack(side="left")

        self.status = tk.Label(self.root, text="Idle", font=("Arial", 10), bg=BG,
                               fg=MUTED, anchor="w")
        self.status.pack(fill="x", padx=14)

        self.progress = ttk.Progressbar(self.root, mode="determinate", maximum=100)
        self.progress.pack(fill="x", padx=14, pady=(4, 12))

    def _browse(self):
        current = self.outdir_var.get().strip()
        if not os.path.isdir(current):
            current = os.path.expanduser("~")
        path = filedialog.askdirectory(initialdir=current, mustexist=True)
        if path:
            self.outdir_var.set(os.path.normpath(path))

    def _open_folder(self):
        path = self.outdir_var.get().strip() or OUT_DIR
        path = os.path.normpath(os.path.expanduser(path))
        if not os.path.isdir(path):
            try:
                os.makedirs(path, exist_ok=True)
            except OSError as e:
                messagebox.showerror("Cannot open folder", str(e))
                return
        os.startfile(path)

    def _read_options(self):
        size = self.size_var.get()
        w, h = next(((w, h) for s, w, h in SIZES if s == size), (1024, 768))
        try:
            count = max(0, int(self.count_var.get() or 0))
        except ValueError:
            raise ValueError("Count must be a whole number (0 = infinite).")
        try:
            interval = max(0.2, float(self.interval_var.get() or 1))
        except ValueError:
            raise ValueError("Interval must be a number of seconds.")
        blur = max(0, min(10, int(self.blur_var.get() or 0)))
        outdir = os.path.normpath(os.path.expanduser(self.outdir_var.get().strip() or OUT_DIR))
        return w, h, count, interval, blur, outdir

    @staticmethod
    def _check_writable(outdir):
        probe = os.path.join(outdir, ".write_test")
        try:
            with open(probe, "wb") as f:
                f.write(b"ok")
        except OSError as e:
            raise ValueError(f"{outdir}\n\n{str(e)}")
        finally:
            try:
                os.remove(probe)
            except OSError:
                pass

    def start(self):
        self._start_worker(single=False)

    def start_single(self):
        self._start_worker(single=True)

    def _start_worker(self, single):
        if self.thread is not None and self.thread.is_alive():
            return

        try:
            w, h, count, interval, blur, outdir = self._read_options()
            os.makedirs(outdir, exist_ok=True)
            self._check_writable(outdir)
        except (ValueError, OSError) as e:
            messagebox.showerror("Cannot save here", str(e))
            return

        if single:
            count = 1

        self.stop_event.clear()
        self.saved = 0
        self.last_outdir = outdir
        self._set_status(f"Saving to {outdir}")
        if count:
            self.progress.configure(mode="determinate", maximum=count, value=0)
        else:
            self.progress.configure(mode="indeterminate")
            self.progress.start(12)
        self.start_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")

        self.thread = threading.Thread(
            target=self._worker,
            args=(w, h, count, interval, blur, self.gray_var.get(), outdir, single),
            daemon=True,
        )
        self.thread.start()

    def stop(self):
        self.stop_event.set()
        self._set_status("Stopping...")

    def _worker(self, w, h, count, interval, blur, gray, outdir, single):
        stamp = time.strftime("%Y%m%d_%H%M%S")
        index = 0
        errors = 0

        while not self.stop_event.is_set():
            index += 1
            if count and index > count:
                break

            query = [f"random={int(time.time() * 1000) % 100000}{index}"]
            if gray:
                query.append("grayscale")
            if blur:
                query.append(f"blur={blur}")
            url = f"{BASE_URL}/{w}/{h}?{'&'.join(query)}"
            path = os.path.join(outdir, f"img_{stamp}_{index:04d}.jpg")

            try:
                self._fetch(url, path)
            except (urllib.error.URLError, OSError, ValueError) as e:
                errors += 1
                self.events.put(("log", f"ERROR #{index}: {e}"))
                if errors >= 5:
                    self.events.put(("error", "5 consecutive failures, stopping."))
                    break
                if self.stop_event.wait(min(5, interval)):
                    break
                continue

            errors = 0
            self.saved += 1
            size_kb = os.path.getsize(path) // 1024
            if index == 1:
                self.events.put(("log", f"Saving to: {outdir}"))
            self.events.put(("log", f"[{index}] saved {os.path.basename(path)} ({size_kb} KB)"))
            self.events.put(("done_one", (path, index, count, outdir)))
            if count and self.saved >= count:
                break
            if self.stop_event.wait(interval):
                break

        self.events.put(("done", (self.saved, errors)))

    @staticmethod
    def _fetch(url, path):
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        tmp = path + ".part"
        with urllib.request.urlopen(req, timeout=30) as resp, open(tmp, "wb") as f:
            if getattr(resp, "status", 200) != 200:
                raise ValueError(f"HTTP {resp.status}")
            total = 0
            while True:
                chunk = resp.read(65536)
                if not chunk:
                    break
                f.write(chunk)
                total += len(chunk)
        if total < 1024:
            os.remove(tmp)
            raise ValueError("response too small")
        os.replace(tmp, path)

    def _save_history(self, path):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, ValueError):
            data = []
        if not isinstance(data, list):
            data = []
        data.append({"file": os.path.basename(path),
                     "size": os.path.getsize(path),
                     "time": time.strftime("%Y-%m-%d %H:%M:%S")})
        try:
            with open(HISTORY_FILE, "w", encoding="utf-8") as f:
                json.dump(data[-500:], f, indent=2)
        except OSError:
            pass

    def _poll_events(self):
        try:
            while True:
                kind, payload = self.events.get_nowait()
                if kind == "log":
                    self._log(payload)
                elif kind == "done_one":
                    path, index, count, outdir = payload
                    self._save_history(path)
                    self._show_preview(path)
                    if count:
                        self.progress.configure(value=index)
                    self._set_status(f"{index} downloaded -> {outdir}")
                elif kind == "error":
                    self._log("ERROR: " + payload)
                    self._set_status("Error")
                elif kind == "done":
                    self._on_done(*payload)
        except queue.Empty:
            pass
        self.root.after(100, self._poll_events)

    def _show_preview(self, path):
        if Image is None or not self.preview_var.get():
            return
        try:
            img = Image.open(path)
            img.thumbnail((420, 320))
            self.preview_photo = ImageTk.PhotoImage(img)
        except (OSError, ValueError):
            return
        self.preview.configure(image=self.preview_photo, text="")

    def _on_done(self, saved, errors):
        if str(self.progress.cget("mode")) == "indeterminate":
            self.progress.stop()
            self.progress.configure(mode="determinate", maximum=100, value=100)
        self.start_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")
        where = self.last_outdir
        if self.stop_event.is_set():
            self._set_status(f"Stopped ({saved} saved) -> {where}")
        elif errors:
            self._set_status(f"Failed after {errors} error(s), {saved} saved -> {where}")
        elif saved == 0:
            self._set_status(f"Nothing saved -> {where}")
        else:
            self._set_status(f"Finished ({saved} saved) -> {where}")

    def _log(self, text):
        self.log_box.configure(state="normal")
        self.log_box.insert("end", text + "\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def _set_status(self, text):
        self.status.configure(text=text)

    def _on_close(self):
        if self.thread is not None and self.thread.is_alive():
            if not messagebox.askyesno("Quit", "A download is running. Stop it and quit?"):
                return
            self.stop_event.set()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    style = ttk.Style()
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass
    style.configure("TProgressbar", troughcolor="#141420", background=ACCENT,
                    bordercolor="#141420", lightcolor=ACCENT, darkcolor=ACCENT)
    style.configure("TCombobox", fieldbackground="#141420", background="#2c2c3c",
                    foreground=FG)
    DownloaderApp(root)
    root.mainloop()
