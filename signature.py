# signature.py
import cv2
import os
import tempfile
from skimage.metrics import structural_similarity as ssim
import requests
from pdf2image import convert_from_path
import numpy as np
from urllib.parse import urlparse

def is_cloudinary_url(url):
    """Check if the URL is a Cloudinary URL"""
    parsed = urlparse(url)
    return 'cloudinary' in parsed.netloc

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
    try:
        # Load the images from various possible sources
        img1 = load_image(path1)
        img2 = load_image(path2)
        
        if img1 is None or img2 is None:
            return -1  # Return -1 if images couldn't be loaded
            
        # turn images to grayscale
        img1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
        img2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
        
        # resize images for comparison
        img1 = cv2.resize(img1, (300, 300))
        img2 = cv2.resize(img2, (300, 300))
        
        # Create a window to display images side by side
        combined = cv2.hconcat([img1, img2])
        cv2.imshow("Signature Comparison", combined)
        cv2.waitKey(1000)  # Show for 1 second
        cv2.destroyAllWindows()
        
        similarity_value = "{:.2f}".format(ssim(img1, img2)*100)
        return float(similarity_value)
        
    except Exception as e:
        print(f"Error in matching: {str(e)}")
        return -1

def checkSimilarity(window, path1, path2):
    """Check similarity between two signatures"""
    if not path1 or not path2:
        messagebox.showerror("Error", "Please select or capture both signatures!")
        return False
        
    result = match(path1=path1, path2=path2)
    
    if result == -1:
        messagebox.showerror("Error", "Failed to process images. Please try again!")
        return False
        
    if(result <= THRESHOLD):
        messagebox.showerror("Failure: Signatures Do Not Match",
                           f"Signatures are {result:.1f}% similar!")
    else:
        messagebox.showinfo("Success: Signatures Match",
                          f"Signatures are {result:.1f}% similar!")
    return True

def capture_image_from_cam_into_temp(sign=1):
    cam = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    if not cam.isOpened():
        messagebox.showerror("Error", "Could not open camera!")
        return False

    cv2.namedWindow("Camera Preview")
    img_captured = False

    while not img_captured:
        ret, frame = cam.read()
        if not ret:
            messagebox.showerror("Error", "Failed to grab frame from camera!")
            break
            
        cv2.imshow("Camera Preview", frame)
        
        k = cv2.waitKey(1)
        if k % 256 == 27:  # ESC pressed
            break
        elif k % 256 == 32:  # SPACE pressed
            if not os.path.isdir('temp'):
                os.makedirs('temp', exist_ok=True)
                
            img_name = f"./temp/test_img{sign}.png"
            
            if cv2.imwrite(filename=img_name, img=frame):
                messagebox.showinfo("Success", "Image captured successfully!")
                img_captured = True
            else:
                messagebox.showerror("Error", "Failed to save image!")
                
    cam.release()
    cv2.destroyAllWindows()
    return img_captured
