import qrcode
from PIL import Image
import cv2
import numpy as np


# =====================================================
# CREATE SINGLE QR
# =====================================================

def create_qr(data: str, color: str, version=5):
    """
    Generate a single colored QR code.
    """
    qr = qrcode.QRCode(
        version=version,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )

    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill_color=color, back_color="white").convert("RGBA")
    return img


# =====================================================
# COMBINE THREE QR CODES INTO RGB_QR
# =====================================================

def combine_qr_images(img_red, img_green, img_blue):
    """
    Combine 3 QR images pixel-wise into one RGB QR.
    """
    size = img_red.size
    final_img = Image.new("RGBA", size)

    red_data = img_red.getdata()
    green_data = img_green.getdata()
    blue_data = img_blue.getdata()

    new_pixels = []

    for i in range(len(red_data)):

        r_pixel = red_data[i][:3] != (255, 255, 255)
        g_pixel = green_data[i][:3] != (255, 255, 255)
        b_pixel = blue_data[i][:3] != (255, 255, 255)

        r = 255 if r_pixel else 0
        g = 255 if g_pixel else 0
        b = 255 if b_pixel else 0

        new_pixels.append((r, g, b, 255))

    final_img.putdata(new_pixels)
    return final_img


def generate_rgb_qr(red_link: str, green_link: str, blue_link: str):
    """
    Generate combined RGB QR from 3 links.
    """
    img_red = create_qr(red_link, "red")
    img_green = create_qr(green_link, "green")
    img_blue = create_qr(blue_link, "blue")

    combined = combine_qr_images(img_red, img_green, img_blue)
    return combined


# =====================================================
# DECODE SECTION
# =====================================================

def decode_single_qr(gray_img):
    """
    Decode a grayscale QR image using OpenCV.
    """
    detector = cv2.QRCodeDetector()
    data, _, _ = detector.detectAndDecode(gray_img)
    return data


def split_and_decode_rgb_qr(pil_image: Image.Image):
    """
    Split RGB QR into 3 layers and decode each.
    """
    img = pil_image.convert("RGBA")
    data = np.array(img)

    threshold = 128  # Important for robustness

    # Create white images
    red_layer = np.ones_like(data) * 255
    green_layer = np.ones_like(data) * 255
    blue_layer = np.ones_like(data) * 255

    # Extract channels
    r_channel = data[:, :, 0]
    g_channel = data[:, :, 1]
    b_channel = data[:, :, 2]

    # Apply threshold
    red_mask = r_channel > threshold
    green_mask = g_channel > threshold
    blue_mask = b_channel > threshold

    # Set black pixels where mask is true
    red_layer[red_mask] = [0, 0, 0, 255]
    green_layer[green_mask] = [0, 0, 0, 255]
    blue_layer[blue_mask] = [0, 0, 0, 255]

    # Convert to grayscale for OpenCV decoding
    red_gray = cv2.cvtColor(red_layer, cv2.COLOR_RGBA2GRAY)
    green_gray = cv2.cvtColor(green_layer, cv2.COLOR_RGBA2GRAY)
    blue_gray = cv2.cvtColor(blue_layer, cv2.COLOR_RGBA2GRAY)

    red_data = decode_single_qr(red_gray)
    green_data = decode_single_qr(green_gray)
    blue_data = decode_single_qr(blue_gray)

    return red_data, green_data, blue_data
