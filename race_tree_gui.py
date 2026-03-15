import customtkinter as ctk
import tkinter.filedialog as fd
import threading
import subprocess
import os
from PIL import Image

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class RaceTreeApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("🏎️ RaceTree 3.0 Pro")
        self.geometry("600x650")

        self.sponsor_images = []
        self.output_filepath = ""
        self.images_dir = ""
        self.process = None

        # --- UI LAYOUT ---
        self.grid_columnconfigure(0, weight=1)

        # Header
        self.header = ctk.CTkLabel(self, text="RaceTree 3.0 Output Generator", font=ctk.CTkFont(size=24, weight="bold"))
        self.header.grid(row=0, column=0, padx=20, pady=(20, 10))

        # Session ID
        self.session_frame = ctk.CTkFrame(self)
        self.session_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        self.session_frame.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(self.session_frame, text="Speedhive Session ID:").grid(row=0, column=0, padx=10, pady=10)
        self.session_entry = ctk.CTkEntry(self.session_frame, placeholder_text="e.g. 10929040")
        self.session_entry.grid(row=0, column=1, padx=10, pady=10, sticky="ew")

        # Grid Source Session ID
        self.grid_frame = ctk.CTkFrame(self)
        self.grid_frame.grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        self.grid_frame.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(self.grid_frame, text="Grid Source Session ID (Opt):").grid(row=0, column=0, padx=10, pady=10)
        self.grid_source_entry = ctk.CTkEntry(self.grid_frame, placeholder_text="e.g. 10839874")
        self.grid_source_entry.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        
        self.generate_grid_checkbox = ctk.CTkCheckBox(self.grid_frame, text="Generate Starting Grid Image?")
        self.generate_grid_checkbox.grid(row=1, column=0, columnspan=2, padx=10, pady=(0, 10), sticky="w")

        self.generate_results_checkbox = ctk.CTkCheckBox(self.grid_frame, text="Generate Official Results Image?")
        self.generate_results_checkbox.grid(row=2, column=0, columnspan=2, padx=10, pady=(0, 10), sticky="w")

        # Output File
        self.output_frame = ctk.CTkFrame(self)
        self.output_frame.grid(row=3, column=0, padx=20, pady=10, sticky="ew")
        self.output_frame.grid_columnconfigure(1, weight=1)
        
        self.btn_output = ctk.CTkButton(self.output_frame, text="Save Output As...", command=self.pick_output_file)
        self.btn_output.grid(row=0, column=0, padx=10, pady=10)
        
        self.lbl_output = ctk.CTkLabel(self.output_frame, text="No file selected.", text_color="gray")
        self.lbl_output.grid(row=0, column=1, padx=10, pady=10, sticky="w")

        # Images Save Folder
        self.images_frame = ctk.CTkFrame(self)
        self.images_frame.grid(row=4, column=0, padx=20, pady=10, sticky="ew")
        self.images_frame.grid_columnconfigure(1, weight=1)
        
        self.btn_images_dir = ctk.CTkButton(self.images_frame, text="Select Images Folder...", command=self.pick_images_dir)
        self.btn_images_dir.grid(row=0, column=0, padx=10, pady=10)
        
        self.lbl_images_dir = ctk.CTkLabel(self.images_frame, text="Root Directory", text_color="gray")
        self.lbl_images_dir.grid(row=0, column=1, padx=10, pady=10, sticky="w")

        # Sponsors Files
        self.sponsor_frame = ctk.CTkFrame(self)
        self.sponsor_frame.grid(row=5, column=0, padx=20, pady=10, sticky="ew")
        self.sponsor_frame.grid_columnconfigure(1, weight=1)
        
        self.btn_sponsors = ctk.CTkButton(self.sponsor_frame, text="Add Sponsor Images (Max 10)", command=self.pick_sponsors)
        self.btn_sponsors.grid(row=0, column=0, padx=10, pady=10)
        
        self.lbl_sponsors = ctk.CTkLabel(self.sponsor_frame, text="0 images selected.", text_color="gray")
        self.lbl_sponsors.grid(row=0, column=1, padx=10, pady=10, sticky="w")
        
        self.sponsor_preview_frame = ctk.CTkScrollableFrame(self.sponsor_frame, orientation="horizontal", height=80)
        self.sponsor_preview_frame.grid(row=1, column=0, columnspan=2, padx=10, pady=(0, 10), sticky="ew")
        
        self.lbl_sponsor_preview_placeholder = ctk.CTkLabel(self.sponsor_preview_frame, text="No logos selected", text_color="gray")
        self.lbl_sponsor_preview_placeholder.pack(pady=20, padx=20)

        # Output Console
        self.console = ctk.CTkTextbox(self, height=150)
        self.console.grid(row=6, column=0, padx=20, pady=10, sticky="nsew")
        self.grid_rowconfigure(6, weight=1)

        # Action Buttons
        self.action_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.action_frame.grid(row=7, column=0, padx=20, pady=20, sticky="ew")
        self.action_frame.grid_columnconfigure((0, 1), weight=1)
        
        self.btn_generate = ctk.CTkButton(self.action_frame, text="GENERATE VIDEO", fg_color="green", hover_color="darkgreen", command=self.start_generation)
        self.btn_generate.grid(row=0, column=0, padx=10, sticky="ew")
        
        self.btn_cancel = ctk.CTkButton(self.action_frame, text="CANCEL", fg_color="red", hover_color="darkred", state="disabled", command=self.cancel_generation)
        self.btn_cancel.grid(row=0, column=1, padx=10, sticky="ew")

    def pick_output_file(self):
        file = fd.asksaveasfilename(defaultextension=".mp4", filetypes=[("MP4 Video", "*.mp4")])
        if file:
            self.output_filepath = file
            self.lbl_output.configure(text=os.path.basename(file), text_color="white")

    def pick_images_dir(self):
        folder = fd.askdirectory(title="Select Output Folder for Images")
        if folder:
            self.images_dir = folder
            self.lbl_images_dir.configure(text=folder, text_color="white")

    def pick_sponsors(self):
        files = fd.askopenfilenames(title="Select Sponsor Images", filetypes=[("Images", "*.png;*.jpg;*.jpeg;*.bmp")])
        if files:
            added = False
            for f in files:
                if f not in self.sponsor_images:
                    if len(self.sponsor_images) >= 10:
                        self.log("⚠️ Warning: Maximum of 10 sponsor images reached. Some selections were ignored.")
                        break
                    self.sponsor_images.append(f)
                    added = True
                    
            if added:
                self.lbl_sponsors.configure(text=f"{len(self.sponsor_images)} images selected.", text_color="white")
                self.update_sponsor_previews()

    def update_sponsor_previews(self):
        # Clear existing previews
        for widget in self.sponsor_preview_frame.winfo_children():
            widget.destroy()
            
        if not self.sponsor_images:
            self.lbl_sponsor_preview_placeholder = ctk.CTkLabel(self.sponsor_preview_frame, text="No logos selected", text_color="gray")
            self.lbl_sponsor_preview_placeholder.pack(pady=20, padx=20)
            return
            
        for img_path in self.sponsor_images:
            try:
                pil_image = Image.open(img_path)
                ctk_image = ctk.CTkImage(light_image=pil_image, dark_image=pil_image, size=(60, 60))
                lbl = ctk.CTkLabel(self.sponsor_preview_frame, image=ctk_image, text="")
                lbl.pack(side="left", padx=5, pady=5)
            except Exception as e:
                print(f"Failed to load preview for {img_path}: {e}")

    def log(self, text):
        self.console.insert("end", text + "\n")
        self.console.see("end")

    def set_gui_state(self, is_running):
        state = "disabled" if is_running else "normal"
        self.session_entry.configure(state=state)
        self.grid_source_entry.configure(state=state)
        self.generate_grid_checkbox.configure(state=state)
        self.generate_results_checkbox.configure(state=state)
        self.btn_output.configure(state=state)
        self.btn_images_dir.configure(state=state)
        self.btn_sponsors.configure(state=state)
        
        if is_running:
            self.btn_generate.configure(state="disabled")
            self.btn_cancel.configure(state="normal")
        else:
            self.btn_generate.configure(state="normal")
            self.btn_cancel.configure(state="disabled")

    def start_generation(self):
        session_id = self.session_entry.get().strip()
        grid_source_id = self.grid_source_entry.get().strip()
        gen_grid = self.generate_grid_checkbox.get() == 1
        gen_results = self.generate_results_checkbox.get() == 1
        if not session_id:
            self.log("❌ Error: You must enter a Speedhive Session ID.")
            return

        self.console.delete("1.0", "end")
        self.set_gui_state(True)
        
        # Run process in separate thread to keep UI responsive
        thread = threading.Thread(target=self.run_pipeline, args=(session_id, grid_source_id, gen_grid, gen_results))
        thread.daemon = True
        thread.start()

    def run_pipeline(self, session_id, grid_source_id, gen_grid, gen_results):
        try:
            # Step 1: Data Fetching. We run race_tree_data.py via Popen.
            self.log(f"--- STEP 1: FETCHING DATA FOR {session_id} ---")
            if grid_source_id:
                self.log(f"            (Using alternate grid from {grid_source_id})")
            
            env = os.environ.copy()
            env["PYTHONIOENCODING"] = "utf-8"
            
            data_cmd = ["python", "f:/RACE_TREE_3.0/race_tree_data.py", session_id]
            if grid_source_id:
                data_cmd.extend(["--grid-source", grid_source_id])
                
            self.process = subprocess.Popen(data_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, encoding='utf-8', errors='replace', env=env, cwd="f:/RACE_TREE_3.0")
            
            for line in self.process.stdout:
                self.log(line.strip())
            
            self.process.wait()
            if self.process.returncode != 0:
                self.log("❌ Error: Data compilation failed.")
                self.set_gui_state(False)
                return
                
            json_file = f"f:/RACE_TREE_3.0/RaceSessionData_{session_id}.json"
            if not os.path.exists(json_file):
                self.log("❌ Error: JSON file was not generated.")
                self.set_gui_state(False)
                return

            # Step 2: Video Generation
            if gen_grid:
                self.log(f"--- STEP 2: GENERATING HIGH-FIDELITY STARTING GRID ---")
                grid_cmd = ["python", "f:/RACE_TREE_3.0/race_tree_grid.py", session_id]
                if self.images_dir:
                    grid_cmd.extend(["--output-dir", self.images_dir])
                self.process = subprocess.Popen(grid_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, encoding='utf-8', errors='replace', env=env, cwd="f:/RACE_TREE_3.0")
                
                for line in self.process.stdout:
                    self.log(line.strip())
                self.process.wait()

            # Step 2.5: Official Results Image Generation
            if gen_results:
                self.log(f"--- STEP 2.5: GENERATING OFFICIAL RESULTS GRID ---")
                results_cmd = ["python", "f:/RACE_TREE_3.0/race_tree_results.py", session_id]
                if self.images_dir:
                    results_cmd.extend(["--output-dir", self.images_dir])
                self.process = subprocess.Popen(results_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, encoding='utf-8', errors='replace', env=env, cwd="f:/RACE_TREE_3.0")
                
                for line in self.process.stdout:
                    self.log(line.strip())
                self.process.wait()

            # Step 3: Video Generation. We run race_tree_video.py via Popen.
            self.log(f"--- STEP 3: RENDERING VIDEO (HARDWARE NVENC) ---")
            
            video_cmd = ["python", "f:/RACE_TREE_3.0/race_tree_video.py", session_id]
            
            if self.output_filepath:
                video_cmd.extend(["--output", self.output_filepath])
            
            if self.sponsor_images:
                video_cmd.append("--sponsors")
                video_cmd.extend(self.sponsor_images)
                
            self.process = subprocess.Popen(video_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, encoding='utf-8', errors='replace', env=env, cwd="f:/RACE_TREE_3.0")
            
            for line in self.process.stdout:
                self.log(line.strip())
                
            self.process.wait()
            
            if self.process.returncode == 0:
                self.log("\n✅ Pipeline Complete! Your video is ready!")
            elif self.process.returncode != -15: # Not terminated by user
                self.log("\n❌ Video Generation Failed.")
                
        except Exception as e:
            self.log(f"Critical Error: {e}")
        finally:
            self.set_gui_state(False)
            self.process = None

    def cancel_generation(self):
        if self.process:
            self.log("\n⚠️ Cancelling running pipeline...")
            
            # Use taskkill to kill the subprocess and its children (ffmpeg) on Windows
            subprocess.call(['taskkill', '/F', '/T', '/PID', str(self.process.pid)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            self.process = None
            self.set_gui_state(False)

if __name__ == "__main__":
    app = RaceTreeApp()
    app.mainloop()
