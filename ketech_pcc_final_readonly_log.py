
import os
import tempfile
from tkinter import Tk, filedialog, Text, Scrollbar, Label, Button, Listbox, END, Frame, DoubleVar
from tkinter.ttk import Style, Progressbar
from datetime import datetime
import mimetypes

SIGNATURES = {
    b"RIFF": ".wav", b"ID3": ".mp3", b"OggS": ".ogg", b"fLaC": ".flac", b"FORM": ".aiff", b".snd": ".au",
    b"MThd": ".mid", b"MAC ": ".ape", b"MPCK": ".mpc", b"AFF\x00": ".aff", b"\x00\x00\x01\x00": ".ttf",
    b"OTTO": ".otf", b"\x1A\x45\xDF\xA3": ".mkv", b"ftypisom": ".mp4", b"ftypmp42": ".mp4",
    b"ftypqt  ": ".mov", b"\x89PNG": ".png", b"\xFF\xD8\xFF": ".jpg", b"GIF89a": ".gif", b"%PDF": ".pdf",
    b"PK\x03\x04": ".zip", b"\x1F\x8B": ".gz", b"Rar!": ".rar", b"7z\xBC": ".7z", b"{": ".json",
    b"<?xml": ".xml", b"<?php": ".php", b"<html": ".html"
}

def guess_extension(data):
    for sig, ext in SIGNATURES.items():
        if data.startswith(sig):
            return ext
    return ".bin"

def is_probably_playable(file_path):
    mime, _ = mimetypes.guess_type(file_path)
    if not mime:
        return False
    return mime.startswith(("audio", "video", "image"))

def extract_chunks(pcc_path, output_dir, log_callback, file_list, progress_callback):
    with open(pcc_path, "rb") as f:
        data = f.read()

    size = len(data)
    offset = 0
    found = 0

    while offset < size:
        ext = guess_extension(data[offset:offset+12])
        end = offset + 12
        while end < size and end - offset < 5_000_000:
            if guess_extension(data[end:end+12]) != ".bin":
                break
            end += 1

        chunk = data[offset:end]
        filename = f"chunk_{found:04d}{ext}"
        file_path = os.path.join(output_dir, filename)
        with open(file_path, "wb") as f_out:
            f_out.write(chunk)

        if is_probably_playable(file_path):
            file_list.append(file_path)
            log_callback(f"[VALID] {filename}\n")
        else:
            junk_path = os.path.join(output_dir, "junk_" + filename)
            os.rename(file_path, junk_path)
            log_callback(f"[JUNK]  {filename}\n")

        found += 1
        offset = end
        progress_callback(offset / size * 100)

    return found

def run_gui():
    root = Tk()
    root.title("KeTech PCC Extractor")
    root.geometry("860x600")
    root.configure(bg="#101010")

    style = Style()
    style.theme_use('clam')
    style.configure("TButton", font=("Helvetica Neue", 12), background="#202020", foreground="#ffffff")
    style.configure("TLabel", font=("Helvetica Neue", 13), background="#101010", foreground="#ffffff")

    header = Label(root, text="KeTech PCC Extractor", font=("Helvetica Neue", 20, "bold"))
    header.pack(pady=10)

    status = Label(root, text="Select a .pcc file to extract.", font=("Helvetica Neue", 12))
    status.pack(pady=5)

    progress_val = DoubleVar()
    progress = Progressbar(root, length=800, variable=progress_val)
    progress.pack(pady=5)

    frame = Frame(root, bg="#101010")
    frame.pack()

    file_listbox = Listbox(frame, bg="#1e1e1e", fg="#ffffff", font=("Helvetica Neue", 10), height=18, width=40)
    file_listbox.grid(row=0, column=1, padx=(5, 10))

    log_box = Text(frame, wrap="word", bg="#1e1e1e", fg="#00ffcc", font=("Menlo", 10), height=18, width=60)
    log_box.grid(row=0, column=0, padx=(10, 5))
    log_box.config(state="disabled")  # Set to read-only

    scrollbar = Scrollbar(frame, command=log_box.yview)
    scrollbar.grid(row=0, column=2, sticky="ns")
    log_box.config(yscrollcommand=scrollbar.set)

    def log_callback(msg):
        log_box.config(state="normal")
        log_box.insert("end", msg)
        log_box.see("end")
        log_box.config(state="disabled")
        root.update()

    extracted_files = []

    def update_progress(pct):
        progress_val.set(pct)
        status.config(text=f"Progress: {pct:.2f}%")
        root.update()

    def browse_file():
        extracted_files.clear()
        file_listbox.delete(0, END)
        log_box.config(state="normal")
        log_box.delete("1.0", "end")
        log_box.config(state="disabled")
        status.config(text="Processing...")
        pcc_file = filedialog.askopenfilename(filetypes=[("PCC files", "*.pcc")])
        if not pcc_file:
            return
        output_dir = filedialog.askdirectory(title="Select Output Folder")
        if not output_dir:
            return
        count = extract_chunks(pcc_file, output_dir, log_callback, extracted_files, update_progress)
        for file in extracted_files:
            file_listbox.insert(END, os.path.basename(file))
        status.config(text=f"Done. Extracted {count} items.")

    Button(root, text="Select .PCC File and Output Folder", command=browse_file).pack(pady=10)
    root.mainloop()

if __name__ == "__main__":
    run_gui()
