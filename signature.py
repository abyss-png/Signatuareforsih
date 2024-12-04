import cv2
import os
import tempfile
from skimage.metrics import structural_similarity as ssim
import requests
from pdf2image import convert_from_path
import numpy as np
from urllib.parse import urlparse
import cloudinary.uploader
from tkinter import messagebox
from PIL import ImageGrab

def is_cloudinary_url(url):
    """Check if the URL is a Cloudinary URL"""
    parsed = urlparse(url)
    return 'cloudinary' in parsed.netloc

def save_signature_file(file_path, user_id):
    """Upload a signature file to Cloudinary and return the file URL."""
    try:
        response = cloudinary.uploader.upload(
            file_path,
            public_id=f"signatures/{user_id}",
            folder="signatures",
            resource_type="auto"  # Auto-detect file type
        )
        return response.get("secure_url")
    except Exception as e:
        print(f"Error uploading file to Cloudinary: {str(e)}")
        return None

def download_image(url):
    """Download image from URL and return as OpenCV image"""
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        image_array = np.asarray(bytearray(response.content), dtype=np.uint8)
        image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
        return image
    except Exception as e:
        print(f"Error downloading image: {str(e)}")
        return None

def extract_first_page_from_pdf(pdf_path):
    """Convert first page of PDF to image"""
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            images = convert_from_path(pdf_path, output_folder=temp_dir, first_page=1, last_page=1)
            if images:
                # Save the first page temporarily
                temp_image_path = os.path.join(temp_dir, 'temp_page.jpg')
                images[0].save(temp_image_path, 'JPEG')
                # Read with OpenCV
                return cv2.imread(temp_image_path)
    except Exception as e:
        print(f"Error converting PDF: {str(e)}")
        return None

def load_image(path):
    """Load image from various sources (local file, URL, or PDF)"""
    try:
        # Check if it's a URL
        if path.startswith('http'):
            return download_image(path)
        
        # Check if it's a PDF
        if path.lower().endswith('.pdf'):
            return extract_first_page_from_pdf(path)
        
        # Regular image file
        return cv2.imread(path)
    
    except Exception as e:
        print(f"Error loading image: {str(e)}")
        return None

def match(path1, path2):
    """Match two images and calculate similarity"""
    try:
        # Load the images from various possible sources
        img1 = load_image(path1)
        img2 = load_image(path2)
        
        if img1 is None or img2 is None:
            return -1  # Return -1 if images couldn't be loaded
            
        # Turn images to grayscale
        img1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
        img2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
        
        # Resize images for comparison
        img1 = cv2.resize(img1, (300, 300))
        img2 = cv2.resize(img2, (300, 300))
        
        # Display images side by side
        combined = cv2.hconcat([img1, img2])
        cv2.imshow("Signature Comparison", combined)
        cv2.waitKey(1000)  # Show for 1 second
        cv2.destroyAllWindows()
        
        # Calculate similarity
        similarity_value = ssim(img1, img2)
        return round(similarity_value * 100, 2)
        
    except Exception as e:
        print(f"Error in matching: {str(e)}")
        return -1

def capture_image_from_cam_into_temp(sign=1):
    """Capture an image from the camera and save it temporarily"""
    try:
        cam = cv2.VideoCapture(0)
        if not cam.isOpened():
            raise Exception("Could not access the camera.")

        cv2.namedWindow("Camera Preview")
        img_captured = False
        frame = None

        while True:
            ret, frame = cam.read()
            if not ret:
                raise Exception("Failed to grab frame from the camera.")

            cv2.imshow("Camera Preview", frame)
            
            key = cv2.waitKey(1)
            if key % 256 == 27:  # ESC key to exit
                break
            elif key % 256 == 32:  # SPACE key to capture
                img_captured = True
                break

        # Release the camera and close the preview window
        cam.release()
        cv2.destroyAllWindows()

        if img_captured and frame is not None:
            # Save the captured image temporarily
            temp_dir = "temp"
            os.makedirs(temp_dir, exist_ok=True)
            img_name = os.path.join(temp_dir, f"test_img{sign}.png")
            cv2.imwrite(img_name, frame)
            return img_name
        else:
            return None

    except Exception as e:
        print(f"Error capturing image: {str(e)}")
        return None

def capture_image_from_clipboard():
    """Capture image from clipboard and save it temporarily"""
    try:
        image = ImageGrab.grabclipboard()

        if image is None:
            raise ValueError("No image found in clipboard.")

        # Save the image as a temporary file
        temp_path = "temp_clipboard_signature.png"
        image.save(temp_path)

        return temp_path

    except Exception as e:
        print(f"Error capturing image from clipboard: {str(e)}")
        return None
