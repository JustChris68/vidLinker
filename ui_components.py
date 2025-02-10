import tkinter as tk
from tkinter import ttk, messagebox
from typing import Any, Callable, Optional
from obswebsocket import obsws, requests, exceptions

class ScrollableFrame(ttk.Frame):
    """A scrollable frame widget"""
    
    def __init__(self, container: Any, *args, **kwargs):
        super().__init__(container, *args, **kwargs)
        
        # Create a canvas and scrollbar
        self.canvas = tk.Canvas(self)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        
        # Create the scrollable frame
        self.scrollable_frame = ttk.Frame(self.canvas)
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        # Add the frame to the canvas
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack everything
        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

class LinkButton(ttk.Frame):
    """A button that copies its link to clipboard when clicked"""
    
    def __init__(self, parent: Any, link: str, description: str):
        super().__init__(parent)
        
        self.link = link
        
        # Create and pack the button
        self.button = ttk.Button(
            self,
            text=description,
            command=self.copy_to_clipboard
        )
        self.button.pack(fill="x", padx=5, pady=2)
    
    def copy_to_clipboard(self) -> None:
        """Copy the link to clipboard"""
        self.clipboard_clear()
        self.clipboard_append(self.link)

class SettingsDialog:
    """Settings dialog for the application"""
    
    def __init__(self, parent, settings):
        self.settings = settings
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Settings")
        self.dialog.geometry("600x400")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.dialog)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Interface tab
        self.setup_interface_tab()
        
        # Video tab
        self.setup_video_tab()
        
        # Audio tab
        self.setup_audio_tab()
        
        # OBS tab
        self.setup_obs_tab()
        
        # Buttons
        button_frame = ttk.Frame(self.dialog)
        button_frame.pack(fill="x", padx=10, pady=10)
        
        ttk.Button(
            button_frame,
            text="Save",
            command=self.apply_settings
        ).pack(side="right", padx=5)
        
        ttk.Button(
            button_frame,
            text="Cancel",
            command=self.dialog.destroy
        ).pack(side="right", padx=5)
    
    def setup_interface_tab(self):
        """Set up interface settings tab"""
        frame = ttk.Frame(self.notebook)
        frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Interface settings
        self.show_labels_var = tk.BooleanVar(value=self.settings.interface.show_labels)
        ttk.Checkbutton(
            frame,
            text="Show Labels",
            variable=self.show_labels_var
        ).pack(anchor="w", pady=5)
        
        self.clean_output_var = tk.BooleanVar(value=self.settings.interface.clean_output)
        ttk.Checkbutton(
            frame,
            text="Clean Output",
            variable=self.clean_output_var
        ).pack(anchor="w", pady=5)
        
        self.debug_mode_var = tk.BooleanVar(value=self.settings.interface.debug_mode)
        ttk.Checkbutton(
            frame,
            text="Debug Mode",
            variable=self.debug_mode_var
        ).pack(anchor="w", pady=5)
        
        self.notebook.add(frame, text="Interface")
    
    def setup_video_tab(self):
        """Set up video settings tab"""
        frame = ttk.Frame(self.notebook)
        frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Resolution
        res_frame = ttk.Frame(frame)
        res_frame.pack(fill="x", pady=5)
        ttk.Label(res_frame, text="Resolution:").pack(side="left")
        self.resolution_var = tk.StringVar(value=self.settings.video.resolution)
        ttk.Entry(
            res_frame,
            textvariable=self.resolution_var
        ).pack(side="left", padx=5)
        
        # Bitrate
        bitrate_frame = ttk.Frame(frame)
        bitrate_frame.pack(fill="x", pady=5)
        ttk.Label(bitrate_frame, text="Bitrate:").pack(side="left")
        self.bitrate_var = tk.StringVar(value=self.settings.video.bitrate)
        ttk.Entry(
            bitrate_frame,
            textvariable=self.bitrate_var
        ).pack(side="left", padx=5)
        
        # FPS
        fps_frame = ttk.Frame(frame)
        fps_frame.pack(fill="x", pady=5)
        ttk.Label(fps_frame, text="FPS:").pack(side="left")
        self.fps_var = tk.StringVar(value=self.settings.video.fps)
        ttk.Entry(
            fps_frame,
            textvariable=self.fps_var
        ).pack(side="left", padx=5)
        
        self.notebook.add(frame, text="Video")
    
    def setup_audio_tab(self):
        """Set up audio settings tab"""
        frame = ttk.Frame(self.notebook)
        frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Audio bitrate
        bitrate_frame = ttk.Frame(frame)
        bitrate_frame.pack(fill="x", pady=5)
        ttk.Label(bitrate_frame, text="Bitrate:").pack(side="left")
        self.audio_bitrate_var = tk.StringVar(value=self.settings.audio.bitrate)
        ttk.Entry(
            bitrate_frame,
            textvariable=self.audio_bitrate_var
        ).pack(side="left", padx=5)
        
        # Stereo
        self.stereo_var = tk.BooleanVar(value=self.settings.audio.stereo)
        ttk.Checkbutton(
            frame,
            text="Stereo Audio",
            variable=self.stereo_var
        ).pack(anchor="w", pady=5)
        
        # Noise suppression
        self.noise_suppression_var = tk.BooleanVar(value=self.settings.audio.noise_suppression)
        ttk.Checkbutton(
            frame,
            text="Noise Suppression",
            variable=self.noise_suppression_var
        ).pack(anchor="w", pady=5)
        
        self.notebook.add(frame, text="Audio")
    
    def setup_obs_tab(self):
        """Set up OBS settings tab"""
        frame = ttk.Frame(self.notebook)
        frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # OBS Enable/Disable toggle
        enable_frame = ttk.Frame(frame)
        enable_frame.pack(fill="x", pady=5)
        
        self.enable_obs_var = tk.BooleanVar(value=self.settings.interface.enable_obs)
        ttk.Checkbutton(
            enable_frame,
            text="Enable OBS Integration",
            variable=self.enable_obs_var,
            command=self.toggle_obs_settings
        ).pack(side="left")
        
        # Connection settings
        self.connection_frame = ttk.LabelFrame(frame, text="Connection Settings")
        self.connection_frame.pack(fill="x", pady=5)
        
        # Host
        host_frame = ttk.Frame(self.connection_frame)
        host_frame.pack(fill="x", pady=5)
        ttk.Label(host_frame, text="Host:").pack(side="left", padx=5)
        self.obs_host_var = tk.StringVar(value=self.settings.obs.host)
        self.host_entry = ttk.Entry(host_frame, textvariable=self.obs_host_var)
        self.host_entry.pack(side="left", fill="x", expand=True)
        
        # Port
        port_frame = ttk.Frame(self.connection_frame)
        port_frame.pack(fill="x", pady=5)
        ttk.Label(port_frame, text="Port:").pack(side="left", padx=5)
        self.obs_port_var = tk.StringVar(value=str(self.settings.obs.port))
        self.port_entry = ttk.Entry(port_frame, textvariable=self.obs_port_var)
        self.port_entry.pack(side="left", fill="x", expand=True)
        
        # Password
        password_frame = ttk.Frame(self.connection_frame)
        password_frame.pack(fill="x", pady=5)
        ttk.Label(password_frame, text="Password:").pack(side="left", padx=5)
        self.obs_password_var = tk.StringVar(value=self.settings.obs.password)
        self.password_entry = ttk.Entry(password_frame, textvariable=self.obs_password_var, show="*")
        self.password_entry.pack(side="left", fill="x", expand=True)
        
        # Test connection button
        test_frame = ttk.Frame(self.connection_frame)
        test_frame.pack(fill="x", pady=5)
        self.test_button = ttk.Button(
            test_frame,
            text="Test Connection",
            command=self.test_obs_connection
        )
        self.test_button.pack(side="right", padx=5)
        
        # Set initial state
        self.toggle_obs_settings()
        
        self.notebook.add(frame, text="OBS")
    
    def toggle_obs_settings(self):
        """Enable/disable OBS settings based on checkbox"""
        enabled = self.enable_obs_var.get()
        state = "normal" if enabled else "disabled"
        
        # Update all entry widgets
        for entry in [self.host_entry, self.port_entry, self.password_entry]:
            entry.configure(state=state)
    
    def test_obs_connection(self):
        """Test the OBS WebSocket connection"""
        if not self.enable_obs_var.get():
            messagebox.showwarning("Warning", "OBS integration is disabled. Please enable it first.")
            return
            
        try:
            # Create temporary OBS manager for testing
            test_manager = OBSManager()
            
            # Try to connect with current settings
            if test_manager.connect(
                host=self.obs_host_var.get(),
                port=int(self.obs_port_var.get()),
                password=self.obs_password_var.get()
            ):
                messagebox.showinfo("Success", "Successfully connected to OBS!")
            else:
                messagebox.showerror("Error", "Failed to connect to OBS. Please check your settings.")
            
            # Clean up test connection
            test_manager.disconnect()
                
        except ValueError:
            messagebox.showerror("Error", "Invalid port number")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to connect to OBS: {str(e)}")
    
    def apply_settings(self):
        """Apply the settings from the dialog"""
        # Interface settings
        self.settings.interface.show_labels = self.show_labels_var.get()
        self.settings.interface.clean_output = self.clean_output_var.get()
        self.settings.interface.debug_mode = self.debug_mode_var.get()
        self.settings.interface.enable_obs = self.enable_obs_var.get()
        
        # Video settings
        self.settings.video.resolution = self.resolution_var.get()
        self.settings.video.bitrate = self.bitrate_var.get()
        self.settings.video.fps = self.fps_var.get()
        
        # Audio settings
        self.settings.audio.bitrate = self.audio_bitrate_var.get()
        self.settings.audio.stereo = self.stereo_var.get()
        self.settings.audio.noise_suppression = self.noise_suppression_var.get()
        
        # OBS settings
        if self.enable_obs_var.get():
            self.settings.obs.host = self.obs_host_var.get()
            try:
                self.settings.obs.port = int(self.obs_port_var.get())
            except ValueError:
                messagebox.showerror("Error", "Port must be a number")
                return False
            self.settings.obs.password = self.obs_password_var.get()
        
        # Save settings
        self.settings.save()
        self.dialog.destroy()
        return True
