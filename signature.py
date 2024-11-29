# signature.py
import cv2
from skimage.metrics import structural_similarity as ssim

def match(path1, path2):
    try:
        # read the images
        img1 = cv2.imread(path1)
        img2 = cv2.imread(path2)
        
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

# main.py modifications - Updated checkSimilarity function
def checkSimilarity(window, path1, path2):
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

# And update the capture_image_from_cam_into_temp function:
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