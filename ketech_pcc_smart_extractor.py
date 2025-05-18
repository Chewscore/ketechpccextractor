
import os
import tempfile
from tkinter import Tk, filedialog, Text, Scrollbar, Label, Button, messagebox, Listbox, END, Frame, DoubleVar
from tkinter.ttk import Style, Progressbar
from datetime import datetime
import mimetypes

SIGNATURES = {
    b"RIFF": ".wav", b"ID3": ".mp3", b"OggS": ".ogg", b"fLaC": ".flac", b"FORM": ".aiff", b".snd": ".au",
    b"MThd": ".mid", b"AFF\x00": ".aff", b"\x00\x00\x01\x00": ".ttf", b"OTTO": ".otf",
    b"\x1A\x45\xDF\xA3": ".mkv", b"\x00\x00\x00\x1Cftypisom": ".mp4",
    b"\x00\x00\x00\x18ftypmp42": ".mp4", b"\x00\x00\x00 ftypqt  ": ".mov",
    b"\x89PNG": ".png", b"\xFF\xD8\xFF\xE0": ".jpg", b"GIF89a": ".gif",
    b"%PDF": ".pdf", b"PK\x03\x04": ".zip", b"\x1F\x8B": ".gz",
}

def is_probably_playable(file_path):
    mime, _ = mimetypes.guess_type(file_path)
    if mime is None:
        return False
    return mime.startswith("audio") or mime.startswith("video") or mime.startswith("image")

def extract_chunks(pcc_path, output_dir, junk_dir, log_callback, file_list, progress_callback):
    with open(pcc_path, "rb") as f:
        data = f.read()

    log_callback("🔍 Starting scan and validation...\n")
    size = len(data)
    offset = 0
    found = 0

    while offset < size:
        matched = False
        for sig, ext in SIGNATURES.items():
            sig_len = len(sig)
            if data[offset:offset+sig_len] == sig:
                end = offset + sig_len
                while end < size and end - offset < 10_000_000:
                    if data[end:end+4] in SIGNATURES.keys():
                        break
                    end += 1
                chunk = data[offset:end]
                filename = f"chunk_{found:04d}{ext}"
                temp_path = os.path.join(output_dir, filename)
                with open(temp_path, "wb") as out_file:
                    out_file.write(chunk)

                if is_probably_playable(temp_path):
                    final_path = os.path.join(output_dir, filename)
                    file_list.append(final_path)
                    log_callback(f"✅ Valid: {filename} at offset {offset}\n")
                else:
                    junk_path = os.path.join(junk_dir, filename)
                    os.rename(temp_path, junk_path)
                    log_callback(f"🚮 Junk: {filename} moved to junk folder\n")

                found += 1
                offset = end
                matched = True
                break
        if not matched:
            offset += 512
        progress_callback(offset / size * 100)

    return found

def run_gui():
    root = Tk()
    root.title("KeTech Smart Extractor")
    root.geometry("800x600")
    root.configure(bg="#f9f9f9")

    style = Style()
    style.theme_use('clam')
    style.configure("TButton", font=("Helvetica Neue", 12))
    style.configure("TLabel", font=("Helvetica Neue", 14), background="#f9f9f9")

    header = Label(root, text="🎧 KeTech .PCC Smart Extractor", font=("Helvetica Neue", 20, "bold"))
    header.pack(pady=10)

    status = Label(root, text="Select a .pcc file to begin.", font=("Helvetica Neue", 13))
    status.pack(pady=5)

    progress_val = DoubleVar()
    progress = Progressbar(root, length=700, variable=progress_val)
    progress.pack(pady=5)

    frame = Frame(root, bg="#f9f9f9")
    frame.pack()

    file_listbox = Listbox(frame, bg="#ffffff", fg="#000000", font=("Helvetica Neue", 10), height=18, width=40)
    file_listbox.grid(row=0, column=1, padx=(5, 10))

    log_box = Text(frame, wrap="word", bg="#f4f4f4", fg="#222", font=("Menlo", 10), height=18, width=60)
    log_box.grid(row=0, column=0, padx=(10, 5))

    scrollbar = Scrollbar(frame, command=log_box.yview)
    scrollbar.grid(row=0, column=2, sticky="ns")
    log_box.config(yscrollcommand=scrollbar.set)

    def log_callback(msg):
        log_box.insert("end", msg)
        log_box.see("end")
        root.update()

    extracted_files = []

    def update_progress(pct):
        progress_val.set(pct)
        status.config(text=f"Progress: {pct:.2f}%")
        root.update()

    def browse_file():
        extracted_files.clear()
        file_listbox.delete(0, END)
        log_box.delete("1.0", "end")
        status.config(text="Processing...")
        file_path = filedialog.askopenfilename(filetypes=[("PCC files", "*.pcc")])
        if not file_path:
            return
        base_dir = tempfile.mkdtemp()
        output_dir = os.path.join(base_dir, "valid")
        junk_dir = os.path.join(base_dir, "junk")
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(junk_dir, exist_ok=True)
        count = extract_chunks(file_path, output_dir, junk_dir, log_callback, extracted_files, update_progress)
        for file in extracted_files:
            file_listbox.insert(END, os.path.basename(file))
        status.config(text=f"✅ Done. {len(extracted_files)} valid, {count - len(extracted_files)} junk.")
        if count == 0:
            messagebox.showinfo("No Files", "No known files were detected.")

    Button(root, text="📁 Select .PCC File", command=browse_file).pack(pady=10)
    root.mainloop()

if __name__ == "__main__":
    run_gui()
