import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pymongo import MongoClient
from pymongo.errors import ConfigurationError
from pymongo.server_api import ServerApi
from dotenv import load_dotenv
from signature import save_signature_file, match, is_cloudinary_url, capture_image_from_cam_into_temp
import cloudinary
import cloudinary.uploader
import os
import requests
from PIL import Image, ImageTk
from io import BytesIO
import signal
import os

# Load environment variables
load_dotenv()

class SignatureVerificationSystem:
    def __init__(self, root):
        self.root = root
        self.root.title("Enhanced Signature Verification System")
        self.root.geometry("800x600")
        
        # Cloudinary configuration
        cloudinary.config(
            cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
            api_key=os.getenv("CLOUDINARY_API_KEY"),
            api_secret=os.getenv("CLOUDINARY_API_SECRET")
        )
        
        # Create main frame
        self.main_frame = ttk.Frame(root, padding="10")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Create and setup GUI elements
        self.setup_gui()
        
        # Initialize database connection
        self.db = self.get_database_connection()

        # Register the window close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def get_database_connection(self):
        """Establish a connection to MongoDB"""
        try:
            mongo_uri = os.getenv("MONGO_URI")
            if not mongo_uri:
                raise ValueError("MongoDB URI not found in environment variables")
            client = MongoClient(mongo_uri, server_api=ServerApi('1'))
            return client.signature_verification
        except ConfigurationError as e:
            messagebox.showerror("Database Error", f"Failed to connect to database: {str(e)}")
            raise

    def setup_gui(self):
        """Setup the GUI elements like labels, buttons, etc."""
        # User ID section
        ttk.Label(self.main_frame, text="User ID:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.user_id_entry = ttk.Entry(self.main_frame, width=40)
        self.user_id_entry.grid(row=0, column=1, columnspan=2, padx=5, pady=5, sticky=tk.W)

        # Signature file section
        ttk.Label(self.main_frame, text="Signature File:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.signature_path_entry = ttk.Entry(self.main_frame, width=40)
        self.signature_path_entry.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)
        
        # File selection buttons
        ttk.Button(self.main_frame, text="Browse File", command=self.select_file).grid(row=1, column=2, padx=5, pady=5)
        ttk.Button(self.main_frame, text="Capture from Camera", command=self.capture_from_camera).grid(row=1, column=3, padx=5, pady=5)
        
        # Action buttons
        ttk.Button(self.main_frame, text="Save Signature", command=self.on_save_signature).grid(row=2, column=1, pady=20)
        ttk.Button(self.main_frame, text="Verify Signature", command=self.on_verify_signature).grid(row=2, column=2, pady=20)
        
        # Status section
        self.status_label = ttk.Label(self.main_frame, text="")
        self.status_label.grid(row=3, column=0, columnspan=4, pady=10)
        
        # Progress bar
        self.progress = ttk.Progressbar(self.main_frame, mode='indeterminate')
        self.progress.grid(row=4, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=10)

    def select_file(self):
        """Open file dialog to select a file (image/PDF)"""
        file_path = filedialog.askopenfilename(
            filetypes=[("All Supported Files", "*.png;*.jpg;*.jpeg;*.bmp;*.pdf"),
                      ("Image Files", "*.png;*.jpg;*.jpeg;*.bmp"),
                      ("PDF Files", "*.pdf"),
                      ("All Files", "*.*")]
        )
        if file_path:
            self.signature_path_entry.delete(0, tk.END)
            self.signature_path_entry.insert(0, file_path)

    def update_status(self, message, is_error=False):
        """Update status label with message"""
        self.status_label.config(text=message, foreground='red' if is_error else 'green')
        self.root.update()

    def start_progress(self):
        """Start progress bar animation"""
        self.progress.start(10)
        self.root.update()

    def stop_progress(self):
        """Stop progress bar animation"""
        self.progress.stop()
        self.root.update()

    def on_save_signature(self):
        """Save signature to Cloudinary and the database"""
        try:
            user_id = self.user_id_entry.get().strip()
            file_path = self.signature_path_entry.get().strip()

            if not user_id or not file_path:
                raise ValueError("User ID and signature file are required")

            self.start_progress()
            self.update_status("Processing signature...")

            # Upload file to Cloudinary if it's a local file
            if not file_path.startswith('http'):
                cloudinary_url = save_signature_file(file_path, user_id)
                if not cloudinary_url:
                    raise Exception("Failed to upload signature to Cloudinary")
            else:
                cloudinary_url = file_path

            # Save to database
            if self.db.signatures.insert_one({"user_id": user_id, "signature_url": cloudinary_url}):
                self.update_status("Signature saved successfully!")
            else:
                raise Exception("Failed to save to database")

        except Exception as e:
            self.update_status(f"Error: {str(e)}", True)
        finally:
            self.stop_progress()

    def capture_from_camera(self):
        """Invoke the camera capture function"""
        img_path = capture_image_from_cam_into_temp()
        if img_path:
            self.signature_path_entry.delete(0, tk.END)
            self.signature_path_entry.insert(0, img_path)
            self.update_status("Captured image from camera successfully!", is_error=False)
        else:
            self.update_status("Error capturing image from camera.", is_error=True)

    def on_verify_signature(self):
        """Verify the user's signature against the database record"""
        try:
            user_id = self.user_id_entry.get().strip()
            new_signature_path = self.signature_path_entry.get().strip()

            if not user_id or not new_signature_path:
                raise ValueError("User ID and signature file are required")

            self.start_progress()
            self.update_status("Verifying signature...")

            # Retrieve existing signature from the database
            user_record = self.db.signatures.find_one({"user_id": user_id})
            if not user_record:
                raise ValueError(f"No signature found for User ID: {user_id}")

            existing_signature_url = user_record.get("signature_url")
            if not existing_signature_url:
                raise ValueError("No existing signature URL found in the database")

            # Automatically download and display the image from Cloudinary
            if is_cloudinary_url(existing_signature_url):
                self.display_image_from_cloudinary(existing_signature_url)

            # Perform signature comparison
            similarity = match(existing_signature_url, new_signature_path)
            if similarity == -1:
                raise ValueError("Failed to process images for comparison")

            similarity_threshold = 75.0  # You can adjust this threshold as needed
            if similarity >= similarity_threshold:
                self.update_status(f"Signatures match! Similarity: {similarity:.2f}%", is_error=False)
                messagebox.showinfo("Verification Successful", f"Signatures are {similarity:.2f}% similar!")
            else:
                self.update_status(f"Signatures do not match. Similarity: {similarity:.2f}%", is_error=True)
                messagebox.showerror("Verification Failed", f"Signatures are only {similarity:.2f}% similar!")

        except Exception as e:
            self.update_status(f"Error: {str(e)}", is_error=True)
        finally:
            self.stop_progress()

    def display_image_from_cloudinary(self, url):
        """Automatically download and display an image from Cloudinary in Tkinter"""
        try:
            # Fetch the image from Cloudinary URL
            response = requests.get(url)
            img_data = BytesIO(response.content)
            
            # Open the image using PIL
            img = Image.open(img_data)
            
            # Convert image to Tkinter-compatible format
            tk_image = ImageTk.PhotoImage(img)
            
            # Display the image on a Tkinter Label or Canvas
            label = ttk.Label(self.main_frame, image=tk_image)
            label.image = tk_image  # Keep a reference to avoid garbage collection
            label.grid(row=5, column=0, columnspan=4)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load image from Cloudinary: {str(e)}")

    def on_close(self):
        """Handle window close event and kill any processes"""
        try:
            # Perform any cleanup or kill processes here
            # For example, if you have camera processes running, stop them:
            # os.system('taskkill /F /IM some_process_name.exe')  # Example of killing a process

            # Close the window gracefully
            self.root.quit()
            self.root.destroy()
        except Exception as e:
            print(f"Error during closing: {str(e)}")
            self.root.quit()
            self.root.destroy()


# To launch the application
def launch_app():
    root = tk.Tk()
    app = SignatureVerificationSystem(root)
    while True:
        try:
            root.update_idletasks()
            root.update()
        except tk.TclError:
            break

launch_app()
