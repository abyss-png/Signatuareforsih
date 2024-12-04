import tkinter as tk
from tkinter import filedialog, messagebox
from pymongo import MongoClient
from pymongo.errors import ConfigurationError
from pymongo.server_api import ServerApi
from datetime import datetime
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

def get_database_connection():
    """
    Establishes connection to MongoDB Atlas using environment variables for security.
    Returns the database connection if successful, None otherwise.
    """
    try:
        # MongoDB Atlas connection string from the .env file
        connection_string = os.getenv('MONGO_URI')
        db_name = os.getenv('DB_NAME')  # Fetch the DB name from the environment

        if not connection_string or not db_name:
            messagebox.showerror(
                "Configuration Error", 
                "MongoDB connection string or database name not found in .env. Please check your environment variables."
            )
            return None

        print(f"Using MongoDB URI: {connection_string}")

        # Create a new client and connect to the server
        client = MongoClient(connection_string, server_api=ServerApi('1'))

        # Send a ping to confirm a successful connection
        client.admin.command('ping')
        print("Pinged your deployment. You successfully connected to MongoDB!")

        # Get the database
        db = client.get_database(db_name)  # Use the DB name from the .env file
        if db is None:
            print("Database is None. Connection may have failed.")
            return None

        return db

    except ConfigurationError as e:
        messagebox.showerror(
            "Database Connection Error",
            f"Could not connect to MongoDB Atlas: {str(e)}\nPlease check your credentials and internet connection."
        )
        return None

def save_signature(user_id, signature_path):
    """
    Saves signature information to MongoDB Atlas.
    """
    try:
        # Ensure user_id and signature_path are strings and not empty
        if not isinstance(user_id, str) or not isinstance(signature_path, str):
            messagebox.showerror("Invalid Input", "User ID and Signature Path must be strings.")
            return False
        
        # Further check to make sure both are non-empty strings
        if not user_id.strip() or not signature_path.strip():
            messagebox.showerror("Invalid Input", "User ID and Signature Path cannot be empty.")
            return False

        # Get the database connection
        db = get_database_connection()
        if db is None:
            return False

        # Access the 'signatures' collection
        signatures_collection = db[os.getenv('COLLECTION_NAME')]  # Collection name from the .env file

        # Explicitly convert user_id and signature_path to strings
        user_id = str(user_id).strip()
        signature_path = str(signature_path).strip()

        # Document to be inserted into the database
        signature_document = {
            "user_id": user_id,  # Ensure it's a string
            "signature_path": signature_path,  # Ensure it's a string
            "timestamp": str(datetime.utcnow()),  # Store the timestamp in UTC as a string
            "status": "active"  # The signature is currently active
        }

        # Insert the document into the collection
        result = signatures_collection.insert_one(signature_document)

        # Check if the signature was inserted
        if result.inserted_id:
            messagebox.showinfo("Success", "Signature saved successfully!")
            return True
        else:
            messagebox.showerror("Error", "Failed to save signature to the database.")
            return False

    except Exception as e:
        messagebox.showerror("Database Error", f"Error saving signature: {str(e)}")
        return False

def verify_signature(user_id, new_signature_path):
    """
    Verifies the saved signature from MongoDB with the newly uploaded signature.
    """
    try:
        # Get the database connection
        db = get_database_connection()
        if db is None:
            return False

        # Access the 'signatures' collection
        signatures_collection = db[os.getenv('COLLECTION_NAME')]  # Collection name from the .env file

        # Find the saved signature for the user
        saved_signature = signatures_collection.find_one({"user_id": user_id})

        if not saved_signature:
            messagebox.showerror("Error", "No saved signature found for the user.")
            return False
        
        # Retrieve the path of the saved signature (this could be used for image comparison)
        saved_signature_path = saved_signature.get('signature_path', None)
        
        if not saved_signature_path:
            messagebox.showerror("Error", "Saved signature path is missing.")
            return False

        # Compare the old and new signature paths (this is a simple string comparison)
        # Here, you can add a more advanced image comparison or hash-based comparison
        if saved_signature_path == new_signature_path:
            messagebox.showinfo("Success", "The signatures match!")
            return True
        else:
            messagebox.showinfo("Result", "The signatures do not match.")
            return False

    except Exception as e:
        messagebox.showerror("Error", f"Error verifying signature: {str(e)}")
        return False

def on_save_signature():
    """Handles the save signature action in the GUI."""
    user_id = user_id_entry.get().strip()  # Get and strip any extra spaces from user ID
    signature_path = signature_path_entry.get().strip()  # Get and strip any extra spaces from signature path

    if not user_id or not signature_path:  # Check if either is empty
        messagebox.showerror("Invalid Input", "User ID and Signature Path cannot be empty.")
        return
    
    if save_signature(user_id, signature_path):
        print("Signature saved successfully!")
    else:
        print("Error saving signature.")

def on_verify_signature():
    """Handles the verify signature action in the GUI."""
    user_id = user_id_entry.get().strip()  # Get and strip any extra spaces from user ID
    new_signature_path = signature_path_entry.get().strip()  # Get and strip any extra spaces from new signature path

    if not user_id or not new_signature_path:  # Check if either is empty
        messagebox.showerror("Invalid Input", "User ID and Signature Path cannot be empty.")
        return
    
    if verify_signature(user_id, new_signature_path):
        print("Signature verified successfully!")
    else:
        print("Error verifying signature.")

def select_file(entry_field):
    """Opens a file dialog to select a file."""
    file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.png;*.jpg;*.jpeg;*.bmp")])
    entry_field.delete(0, tk.END)  # Clear the current content in the entry field
    entry_field.insert(0, file_path)  # Insert the selected file path

# Create the Tkinter GUI application
root = tk.Tk()
root.title("Signature Verification System")
root.geometry("600x400")

# Create GUI elements
tk.Label(root, text="User ID").grid(row=0, column=0, padx=10, pady=10)
user_id_entry = tk.Entry(root, width=40)
user_id_entry.grid(row=0, column=1, padx=10)

tk.Label(root, text="Signature Path").grid(row=1, column=0, padx=10, pady=10)
signature_path_entry = tk.Entry(root, width=40)
signature_path_entry.grid(row=1, column=1, padx=10)

# Browse button
tk.Button(root, text="Browse", command=lambda: select_file(signature_path_entry)).grid(row=1, column=2)

# Save Signature button
tk.Button(root, text="Save Signature", command=on_save_signature).grid(row=2, column=1, pady=10)

# Verify Signature button
tk.Button(root, text="Verify Signature", command=on_verify_signature).grid(row=3, column=1, pady=10)

root.mainloop()
