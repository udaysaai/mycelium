import os
import cv2
import numpy as np
from PIL import Image, ImageSequence

def convert_webp_to_mp4(input_path, output_path):
    print(f"Opening {input_path} with Pillow...")
    try:
        img = Image.open(input_path)
        
        # Get frame dimensions
        width, height = img.size
        
        # Get metadata
        duration = img.info.get('duration', 100)
        fps = 1000 / duration if duration > 0 else 10
        
        print(f"Dimensions: {width}x{height}, FPS: {fps:.2f}. Starting encoding...")
        
        # Define the codec and create VideoWriter object
        # 'mp4v' or 'XVID' are generally safe
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        
        for i, frame in enumerate(ImageSequence.Iterator(img)):
            if i % 20 == 0:
                print(f"Processing frame {i}...")
            
            # Convert PIL frame to RGB
            rgb_frame = frame.convert("RGB")
            # Convert to numpy and then to BGR for OpenCV
            numpy_frame = np.array(rgb_frame)
            bgr_frame = cv2.cvtColor(numpy_frame, cv2.COLOR_RGB2BGR)
            
            out.write(bgr_frame)
            
        out.release()
        img.close()
        print("Conversion complete!")
    except Exception as e:
        print(f"Error during conversion: {e}")

if __name__ == "__main__":
    input_file = r"C:\Users\Uday\.gemini\antigravity\brain\fca18f3e-bc15-439c-9af7-f8c992955f33\hosted_promo_b_roll_1776681180073.webp"
    output_file = r"C:\Users\Uday\.gemini\antigravity\brain\fca18f3e-bc15-439c-9af7-f8c992955f33\hosted_promo_b_roll.mp4"
    
    if os.path.exists(input_file):
        convert_webp_to_mp4(input_file, output_file)
    else:
        print(f"Error: Could not find the source file at {input_file}")
