# gui.py — FINAL COMBINED VERSION (WITH REDO + ALL ORIGINAL FEATURES)

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from PIL import Image, ImageTk, ImageFilter, ImageEnhance
import threading
import queue
import os
import webbrowser
import logging

from recommender import RecommenderEngine
from ytm_client import YTMusicClient
from models import Playlist
from voice_handler import VoiceRecognizer

logger = logging.getLogger(__name__)
BACKGROUND_IMAGE_PATH = "data/bg_smart_playlist.jpg"

SPOTIFY_GREEN = "#1DB954"
SPOTIFY_GREEN_HOVER = "#1ED760"
BG_DARK = "#121613"
BG_SIDEBAR = "#181a1d"
BG_PANEL = "#1b1d22"


class SmartPlaylistGUI:
    def __init__(self, recommender=None, ytm_client=None):

        # INIT CLIENT
        if ytm_client is None:
            try:
                self.yt_client = YTMusicClient()
            except:
                self.yt_client = None
        else:
            self.yt_client = ytm_client

        self.engine = recommender or RecommenderEngine(self.yt_client)

        # ROOT FIRST
        self.root = tk.Tk()
        self.root.title("Smart Playlist Generator Based on Mood & Activity — By Afdal.")
        self.root.geometry("1100x720")
        self.root.minsize(900, 600)

        # STATE
        self.result_queue = queue.Queue()
        self.current_playlist = Playlist("(kosong)")
        self.undo_stack = []
        self.redo_stack = []        # NEW
        self.is_generating = False

        # BACKGROUND
        self.bg_img = self._load_background(BACKGROUND_IMAGE_PATH)
        self.bg_label = tk.Label(self.root, image=self.bg_img)
        self.bg_label.place(relx=0, rely=0, relwidth=1, relheight=1)

        # MAIN CONTAINER
        self.container = tk.Frame(self.root, bg=BG_DARK)
        self.container.pack(fill="both", expand=True, padx=20, pady=20)

        # BUILD UI
        self._build_layout()

        # Voice recognizer
        self.voice = VoiceRecognizer(self._voice_callback_from_thread)

        # Queue polling
        self.root.after(200, self._poll_queue)

    # ============================
    # BACKGROUND IMAGE
    # ============================
    def _load_background(self, path):
        try:
            img = Image.open(path).convert("RGB")
        except:
            img = Image.new("RGB", (1100, 720), (20, 20, 20))
        img = img.resize((1100, 720), Image.LANCZOS)
        img = img.filter(ImageFilter.GaussianBlur(8))
        img = ImageEnhance.Brightness(img).enhance(0.32)
        return ImageTk.PhotoImage(img)

    # ============================
    # BUILD UI LAYOUT
    # ============================
    def _build_layout(self):

        # ===================== SIDEBAR =======================
        sidebar = tk.Frame(self.container, bg=BG_SIDEBAR, padx=16, pady=16)
        sidebar.place(relx=0.03, rely=0.05, relwidth=0.26, relheight=0.9)

        tk.Label(
            sidebar, text="Smart Playlist",
            font=("Segoe UI", 18, "bold"),
            fg=SPOTIFY_GREEN, bg=BG_SIDEBAR
        ).pack(anchor="w", pady=(0, 20))

        # Mood
        tk.Label(sidebar, text="Mood", bg=BG_SIDEBAR, fg="white").pack(anchor="w")
        self.mood_var = tk.StringVar(value="chill")
        ttk.Combobox(
            sidebar,
            values=["chill", "energetic", "happy", "sad", "focus", "romantic", "party"],
            textvariable=self.mood_var,
            state="readonly"
        ).pack(anchor="w", fill="x")

        # Activity
        tk.Label(sidebar, text="Activity", bg=BG_SIDEBAR, fg="white").pack(anchor="w", pady=(8, 0))
        self.act_var = tk.StringVar(value="study")
        ttk.Combobox(
            sidebar,
            values=["study", "workout", "relax", "sleep", "commute", "work"],
            textvariable=self.act_var,
            state="readonly"
        ).pack(anchor="w", fill="x")

        # Time
        tk.Label(sidebar, text="Time of Day", bg=BG_SIDEBAR, fg="white").pack(anchor="w", pady=(8, 0))
        self.time_var = tk.StringVar(value="night")
        ttk.Combobox(
            sidebar,
            values=["morning", "afternoon", "evening", "night"],
            textvariable=self.time_var,
            state="readonly"
        ).pack(anchor="w", fill="x")

        # Genre
        tk.Label(sidebar, text="Genre (optional)", bg=BG_SIDEBAR, fg="white").pack(anchor="w", pady=(8, 0))
        self.genre_var = tk.StringVar()
        ttk.Entry(sidebar, textvariable=self.genre_var).pack(anchor="w", fill="x")

        # Count
        tk.Label(sidebar, text="Track Count", bg=BG_SIDEBAR, fg="white").pack(anchor="w", pady=(8, 0))
        self.count_var = tk.IntVar(value=12)
        ttk.Spinbox(sidebar, from_=5, to=30, textvariable=self.count_var).pack(anchor="w")

        # BUTTONS (Generate, Undo, Redo)
        btn_frame = tk.Frame(sidebar, bg=BG_SIDEBAR)
        btn_frame.pack(side="bottom", fill="x", pady=10)

        tk.Button(btn_frame, text="🎵 Generate", bg=SPOTIFY_GREEN, fg="black",
                  font=("Segoe UI", 12, "bold"), command=self._start_generate_thread).pack(fill="x", pady=4)

        tk.Button(btn_frame, text="🔙 Undo", bg="#bf1616", fg="white",
                  font=("Segoe UI", 12, "bold"), command=self._undo).pack(fill="x", pady=4)

        tk.Button(btn_frame, text="🔁 Redo", bg="#145214", fg="white",
                  font=("Segoe UI", 12, "bold"), command=self._redo).pack(fill="x", pady=4)

        # Voice button
        self.voice_btn = tk.Button(
            btn_frame, text="🎤 Hold to Speak",
            bg="#2e2e2e", fg="white", font=("Segoe UI", 12, "bold")
        )
        self.voice_btn.pack(fill="x", pady=4)
        self.voice_btn.bind("<ButtonPress-1>", self._on_voice_press)
        self.voice_btn.bind("<ButtonRelease-1>", self._on_voice_release)

        # ===================== MAIN PANEL =======================
        panel = tk.Frame(self.container, bg=BG_PANEL)
        panel.place(relx=0.32, rely=0.05, relwidth=0.65, relheight=0.9)

        hdr = tk.Frame(panel, bg=BG_PANEL)
        hdr.pack(fill="x", pady=(6, 8), padx=10)

        tk.Label(
            hdr, text="Generated Playlist",
            font=("Segoe UI", 14, "bold"),
            fg="white", bg=BG_PANEL
        ).pack(side="top")

        self.status_var = tk.StringVar(value="Ready")
        tk.Label(hdr, textvariable=self.status_var, bg=BG_PANEL, fg="#aaaaaa").pack(side="top")

        # TREEVIEW
        tree_frame = tk.Frame(panel, bg=BG_PANEL)
        tree_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        scrollbar = ttk.Scrollbar(tree_frame)
        scrollbar.pack(side="right", fill="y")

        cols = ("No", "Title", "Channel", "Duration")
        self.tree = ttk.Treeview(tree_frame, columns=cols, show="headings", yscrollcommand=scrollbar.set)

        for c in cols:
            self.tree.heading(c, text=c)
            width = 350 if c == "Title" else 120
            self.tree.column(c, width=width)

        self.tree.pack(fill="both", expand=True)
        scrollbar.config(command=self.tree.yview)

        # Double-click open
        self.tree.bind("<Double-1>", lambda e: self._open_selected())

        # BOTTOM BUTTONS (Open, Save TXT, Save JSON)
        btn_row = tk.Frame(panel, bg=BG_PANEL)
        btn_row.pack(fill="x", pady=(8, 6), padx=10)

        tk.Button(btn_row, text="▶️ Open Selected", fg="white", bg="#2e2e2e",
                  command=self._open_selected).pack(side="left", padx=4)

        tk.Button(btn_row, text="💾 Save TXT", fg="white", bg="#2e2e2e",
                  command=self._save_txt).pack(side="left", padx=4)

        tk.Button(btn_row, text="💾 Save JSON", fg="white", bg="#2e2e2e",
                  command=self._save_json).pack(side="left", padx=4)

    # ==========================================================
    # GENERATE THREAD
    # ==========================================================
    def _start_generate_thread(self):
        if self.is_generating:
            return

        self.is_generating = True
        self.status_var.set("Generating...")

        # Save UNDO
        if self.current_playlist.tracks:
            self.undo_stack.append(self.current_playlist.clone())

        # Generate action clears redo
        self.redo_stack.clear()

        threading.Thread(target=self._generate_background, daemon=True).start()

    def _generate_background(self):
        try:
            playlist, query = self.engine.generate(
                mood=self.mood_var.get(),
                activity=self.act_var.get(),
                time_of_day=self.time_var.get(),
                genre=self.genre_var.get().strip() or None,
                top_n=int(self.count_var.get())
            )
            self.result_queue.put(("ok", playlist, query))
        except Exception as e:
            self.result_queue.put(("err", str(e)))

    # ==========================================================
    # QUEUE HANDLER
    # ==========================================================
    def _poll_queue(self):
        try:
            item = self.result_queue.get_nowait()
        except queue.Empty:
            self.root.after(200, self._poll_queue)
            return

        if item[0] == "ok":
            playlist, query = item[1], item[2]
            self._apply_playlist(playlist)
            self.status_var.set(f"✓ {query}")
        else:
            messagebox.showerror("Error", item[1])
            self.status_var.set("Error")

        self.is_generating = False
        self.root.after(200, self._poll_queue)

    # ==========================================================
    # APPLY PLAYLIST
    # ==========================================================
    def _apply_playlist(self, playlist: Playlist):
        self.current_playlist = playlist
        self.tree.delete(*self.tree.get_children())

        for i, track in enumerate(playlist.tracks, 1):
            self.tree.insert("", "end", values=(i, track.title, track.channel, track.duration))

    # ==========================================================
    # UNDO / REDO
    # ==========================================================
    def _undo(self):

        if not self.undo_stack:
            messagebox.showinfo("Undo", "Tidak ada history untuk di-undo.")
            return

        # Push current → redo
        self.redo_stack.append(self.current_playlist.clone())

        # Pop undo
        self.current_playlist = self.undo_stack.pop()
        self._apply_playlist(self.current_playlist)
        self.status_var.set("Undo applied")

    def _redo(self):

        if not self.redo_stack:
            messagebox.showinfo("Redo", "Tidak ada history untuk di-redo.")
            return

        # Push current → undo
        self.undo_stack.append(self.current_playlist.clone())

        # Pop redo
        self.current_playlist = self.redo_stack.pop()
        self._apply_playlist(self.current_playlist)
        self.status_var.set("Redo applied")

    # ==========================================================
    # OPEN SELECTED
    # ==========================================================
    def _open_selected(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Open", "Please select a track")
            return

        idx = self.tree.index(sel[0])
        track = self.current_playlist.tracks[idx]

        if track.video_id:
            webbrowser.open(f"https://music.youtube.com/watch?v={track.video_id}")
        elif track.url:
            webbrowser.open(track.url)
        else:
            messagebox.showinfo("Open", "Track has no URL")

    # ==========================================================
    # SAVE TXT / JSON
    # ==========================================================
    def _save_txt(self):
        if not self.current_playlist.tracks:
            messagebox.showwarning("Save", "Playlist empty")
            return

        os.makedirs("data/saved_playlists", exist_ok=True)

        path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            initialdir="data/saved_playlists",
            filetypes=[("Text files", "*.txt")]
        )
        if path:
            self.current_playlist.export_txt(path)
            messagebox.showinfo("Saved", f"Playlist saved to:\n{path}")

    def _save_json(self):
        if not self.current_playlist.tracks:
            messagebox.showwarning("Save", "Playlist empty")
            return

        os.makedirs("data/saved_playlists", exist_ok=True)

        path = filedialog.asksaveasfilename(
            defaultextension=".json",
            initialdir="data/saved_playlists",
            filetypes=[("JSON files", "*.json")]
        )
        if path:
            self.current_playlist.export_json(path)
            messagebox.showinfo("Saved", f"Playlist saved to:\n{path}")

    # ==========================================================
    # VOICE COMMAND
    # ==========================================================
    def _on_voice_press(self, e):
        self.voice_btn.config(text="🎤 Listening...", bg=SPOTIFY_GREEN)
        self.voice.start_listening()

    def _on_voice_release(self, e):
        self.voice_btn.config(text="🎤 Processing...", bg="#2e2e2e")
        self.voice.stop_listening()

    def _voice_callback_from_thread(self, text):
        def apply():
            if not text:
                return
            if "buat" in text.lower() or "generate" in text.lower():
                self._start_generate_thread()
        self.root.after(0, apply)

    # RUN
    def run(self):
        self.root.mainloop()
