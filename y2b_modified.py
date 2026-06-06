import tkinter as tk
from tkinter import messagebox, ttk
import threading
import yt_dlp

check_timer = None
playlist_checked = False
stop_download = False
total_items = 1
completed_items = 0
current_title = ""


class DownloadStopped(Exception):
    pass


def set_status(text):
    status_text.config(text=text)


def update_download_button():
    choice = format_var.get()
    if choice == "audio_playlist":
        download_button.config(state="normal" if playlist_checked else "disabled")
    else:
        download_button.config(state="normal")


def paste_url():
    try:
        url_entry.delete(0, tk.END)
        url_entry.insert(0, root.clipboard_get())
        on_url_change()
    except:
        messagebox.showerror("Error", "Clipboard is empty")


def select_format(value):
    format_var.set(value)

    for key, frame in option_frames.items():
        frame.config(bg="#f5f5f7")

    option_frames[value].config(bg="#fff2f2")

    if value == "audio_playlist":
        on_url_change()
    else:
        update_download_button()


def progress_hook(d):
    global completed_items, stop_download, current_title

    if stop_download:
        raise DownloadStopped("Download stopped by user")

    if d["status"] == "downloading":
        filename = d.get("filename", "")
        current_title = filename.split("\\")[-1].split("/")[-1]

        total = d.get("total_bytes") or d.get("total_bytes_estimate")
        downloaded = d.get("downloaded_bytes", 0)

        percent = 0
        if total:
            percent = downloaded / total * 100

        progress_bar["value"] = completed_items
        percent_label.config(text=f"{int((completed_items / total_items) * 100)}%")
        set_status(f"Downloading... {completed_items + 1} / {total_items} songs")
        current_label.config(text=f'Currently processing: "{current_title}"')

    elif d["status"] == "finished":
        completed_items += 1
        progress_bar["value"] = completed_items
        percent_label.config(text=f"{int((completed_items / total_items) * 100)}%")
        set_status(f"Downloading... {completed_items} / {total_items} songs")


def auto_check_playlist_count():
    global playlist_checked, total_items

    url = url_entry.get().strip()
    playlist_checked = False
    update_download_button()

    if not url:
        playlist_count_label.config(text="")
        return

    try:
        set_status("Checking playlist...")
        playlist_count_label.config(text="Checking URL...")

        ydl_opts = {
            "quiet": True,
            "extract_flat": True,
            "skip_download": True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

        if "entries" in info and info["entries"]:
            total_items = len(list(info["entries"]))
            playlist_count_label.config(text=f"Playlist contains {total_items} songs/videos")
        else:
            total_items = 1
            playlist_count_label.config(text="Single video detected")

        progress_bar["maximum"] = total_items
        playlist_checked = True
        set_status("Ready to download")

    except Exception as e:
        playlist_checked = False
        playlist_count_label.config(text="Could not check playlist")
        set_status("Invalid URL or check failed")

    update_download_button()


def on_url_change(event=None):
    global check_timer, playlist_checked

    playlist_checked = False
    update_download_button()

    if check_timer:
        root.after_cancel(check_timer)

    check_timer = root.after(900, lambda: threading.Thread(target=auto_check_playlist_count, daemon=True).start())


def stop_current_download():
    global stop_download
    stop_download = True
    set_status("Stopping download...")
    stop_button.config(state="disabled")


def download():
    global stop_download, completed_items, total_items

    url = url_entry.get().strip()
    choice = format_var.get()

    if not url:
        messagebox.showerror("Error", "Please enter a YouTube URL")
        return

    if choice == "audio_playlist" and not playlist_checked:
        messagebox.showerror("Error", "Please wait until playlist count is checked")
        return

    stop_download = False
    completed_items = 0

    if choice in ["video", "audio_single"]:
        total_items = 1

    progress_bar["maximum"] = total_items
    progress_bar["value"] = 0
    percent_label.config(text="0%")

    download_button.config(state="disabled")
    stop_button.config(state="normal")

    if choice == "video":
        ydl_opts = {
            "outtmpl": "%(title)s.%(ext)s",
            "noplaylist": True,
            "format": "bestvideo+bestaudio/best",
            "merge_output_format": "mp4",
            "progress_hooks": [progress_hook],
        }

    elif choice == "audio_single":
        ydl_opts = {
            "outtmpl": "%(title)s.%(ext)s",
            "noplaylist": True,
            "format": "bestaudio/best",
            "progress_hooks": [progress_hook],
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "320",
            }],
        }

    else:
        ydl_opts = {
            "outtmpl": "%(playlist_title)s/%(title)s.%(ext)s",
            "noplaylist": False,
            "format": "bestaudio/best",
            "progress_hooks": [progress_hook],
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "320",
            }],
        }

    try:
        set_status(f"Downloading... 1 / {total_items} songs")

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        if not stop_download:
            set_status("Download completed!")
            percent_label.config(text="100%")
            current_label.config(text="All files downloaded successfully")

    except DownloadStopped:
        set_status(f"Stopped at {completed_items} / {total_items} songs")
        messagebox.showinfo("Stopped", "Download stopped by user")

    except Exception as e:
        set_status("Download failed")
        messagebox.showerror("Error", str(e))

    stop_button.config(state="disabled")
    update_download_button()


def start_download_thread():
    threading.Thread(target=download, daemon=True).start()


root = tk.Tk()
root.title("YouTube Downloader")
root.geometry("390x900")
root.configure(bg="#f7f7fb")
root.resizable(False, False)

format_var = tk.StringVar(value="video")

style = ttk.Style()
style.theme_use("default")
style.configure(
    "red.Horizontal.TProgressbar",
    troughcolor="#eeeeee",
    background="#d40011",
    thickness=8,
    borderwidth=0,
)

def card(parent, pady=12):
    f = tk.Frame(parent, bg="white", padx=22, pady=20)
    f.pack(fill="x", padx=22, pady=pady)
    return f


# URL CARD
url_card = card(root, 18)

tk.Label(
    url_card,
    text="Ready to Download?",
    bg="white",
    fg="#20212a",
    font=("Segoe UI", 13, "bold")
).pack(anchor="w")

url_box = tk.Frame(url_card, bg="#f0f0f3", padx=10, pady=8)
url_box.pack(fill="x", pady=(14, 0))

tk.Label(url_box, text="🔗", bg="#f0f0f3", fg="#8a90a0", font=("Segoe UI", 13)).pack(side="left")

url_entry = tk.Entry(
    url_box,
    bd=0,
    bg="#f0f0f3",
    fg="#2a2a2a",
    insertbackground="#2a2a2a",
    font=("Segoe UI", 11)
)
url_entry.pack(side="left", fill="x", expand=True, padx=8)
url_entry.insert(0, "")
url_entry.bind("<KeyRelease>", on_url_change)

tk.Button(
    url_box,
    text="Paste",
    command=paste_url,
    bg="white",
    fg="#d40011",
    activebackground="white",
    activeforeground="#d40011",
    bd=0,
    padx=14,
    pady=8,
    font=("Segoe UI", 10, "bold")
).pack(side="right")


# FORMAT CARD
format_card = card(root, 10)

tk.Label(
    format_card,
    text="Select Format",
    bg="white",
    fg="#20212a",
    font=("Segoe UI", 13, "bold")
).pack(anchor="w", pady=(0, 16))

option_frames = {}

def option(value, icon, title, subtitle):
    f = tk.Frame(format_card, bg="#f5f5f7", padx=16, pady=14)
    f.pack(fill="x", pady=7)
    option_frames[value] = f

    tk.Label(f, text=icon, bg=f["bg"], fg="#d40011", font=("Segoe UI", 18)).pack(side="left", padx=(0, 16))

    text_area = tk.Frame(f, bg=f["bg"])
    text_area.pack(side="left", fill="x", expand=True)

    tk.Label(
        text_area,
        text=title,
        bg=f["bg"],
        fg="#20212a",
        font=("Segoe UI", 11, "bold")
    ).pack(anchor="w")

    tk.Label(
        text_area,
        text=subtitle,
        bg=f["bg"],
        fg="#818796",
        font=("Segoe UI", 10)
    ).pack(anchor="w")

    rb = tk.Radiobutton(
        f,
        variable=format_var,
        value=value,
        command=lambda: select_format(value),
        bg=f["bg"],
        activebackground=f["bg"],
        selectcolor="white"
    )
    rb.pack(side="right")

    for widget in [f, text_area]:
        widget.bind("<Button-1>", lambda e, v=value: select_format(v))

option("video", "▣", "Video MP4", "Highest quality available")
option("audio_single", "♪", "Audio MP3 - Single File", "320kbps high fidelity")
option("audio_playlist", "♬", "Audio MP3 - Full Playlist", "Batch process all tracks")




# PROGRESS CARD
progress_card = card(root, 10)

top_progress = tk.Frame(progress_card, bg="white")
top_progress.pack(fill="x")

status_text = tk.Label(
    top_progress,
    text="Ready",
    bg="white",
    fg="#d40011",
    font=("Segoe UI", 11, "bold")
)
status_text.pack(side="left")

percent_label = tk.Label(
    top_progress,
    text="0%",
    bg="white",
    fg="#8a90a0",
    font=("Segoe UI", 11, "bold")
)
percent_label.pack(side="right")

progress_bar = ttk.Progressbar(
    progress_card,
    length=300,
    mode="determinate",
    style="red.Horizontal.TProgressbar"
)
progress_bar.pack(fill="x", pady=14)

current_label = tk.Label(
    progress_card,
    text='Currently processing: "-”',
    bg="white",
    fg="#9aa0ad",
    font=("Segoe UI", 10, "italic"),
    wraplength=300,
    justify="center"
)
current_label.pack()

playlist_count_label = tk.Label(
    progress_card,
    text="",
    bg="white",
    fg="#777",
    font=("Segoe UI", 9)
)
playlist_count_label.pack(pady=(8, 0))


# BUTTONS
download_button = tk.Button(
    root,
    text="⬇  Download",
    command=start_download_thread,
    bg="#d40011",
    fg="white",
    activebackground="#b8000e",
    activeforeground="white",
    bd=0,
    height=2,
    font=("Segoe UI", 12, "bold")
)
download_button.pack(fill="x", padx=22, pady=(12, 10))

stop_button = tk.Button(
    root,
    text="⏹  Stop",
    command=stop_current_download,
    bg="white",
    fg="#666",
    activebackground="#f2f2f2",
    activeforeground="#666",
    bd=0,
    height=2,
    font=("Segoe UI", 11, "bold"),
    state="disabled"
)
stop_button.pack(fill="x", padx=22, pady=(0, 12))

select_format("video")

update_download_button()

root.mainloop()