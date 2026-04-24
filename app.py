
import streamlit as st
import qrcode
import zlib
import base64
import numpy as np
from PIL import Image
import cv2
import io
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

# ---------------- PAGE CONFIG ---------------- #
st.set_page_config(page_title="RGB QR System", layout="centered")

# ---------------- SESSION STATE ---------------- #
if "mode" not in st.session_state:
    st.session_state.mode = "Encode"

# ---------------- SIDEBAR ---------------- #
st.sidebar.title("Dashboard")

st.sidebar.info("""
Features:
- AES Encryption
- Compression (zlib)
- RGB QR Encoding
- Camera Scan
""")

st.sidebar.markdown("---")

# ---------------- FIXED AES KEY ---------------- #
key = b'1234567890123456'

# ---------------- HEADER ---------------- #
st.markdown("""
<h1 style='text-align: center; color: white;'>RGB QR Code System</h1>
<p style='text-align: center;'>Secure Compressed Encrypted QR</p>
""", unsafe_allow_html=True)

# ---------------- MODE SELECT ---------------- #
mode = st.radio("Select Mode", ["Encode", "Decode"], horizontal=True)
st.session_state.mode = mode
st.sidebar.write("Current Mode:", st.session_state.mode)

# ---------------- AES FUNCTIONS ---------------- #
def encrypt_data(data, key):
    cipher = AES.new(key, AES.MODE_CBC)
    return cipher.iv + cipher.encrypt(pad(data, AES.block_size))

def decrypt_data(enc_data, key):
    iv = enc_data[:16]
    ct = enc_data[16:]
    cipher = AES.new(key, AES.MODE_CBC, iv)
    return unpad(cipher.decrypt(ct), AES.block_size)

# ---------------- QR GENERATION ---------------- #
def generate_qr(data):
    qr = qrcode.QRCode(
        version=None,
        box_size=10,  # increased for better readability
        border=2
    )
    qr.add_data(data)
    qr.make(fit=True)
    return qr.make_image(fill_color="black", back_color="white")

# ---------------- RGB FUNCTIONS ---------------- #
def merge_rgb(r, g, b):
    r, g, b = r.convert("L"), g.convert("L"), b.convert("L")

    min_w = min(r.width, g.width, b.width)
    min_h = min(r.height, g.height, b.height)

    r, g, b = r.resize((min_w, min_h)), g.resize((min_w, min_h)), b.resize((min_w, min_h))

    return Image.fromarray(np.stack([
        np.array(r), np.array(g), np.array(b)
    ], axis=2).astype('uint8'))

def split_rgb(image):
    img = np.array(image)
    return (
        Image.fromarray(img[:, :, 0]),
        Image.fromarray(img[:, :, 1]),
        Image.fromarray(img[:, :, 2])
    )

# ---------------- ROBUST QR DECODER ---------------- #
def decode_qr(img, detector):
    img = np.array(img)

    # ✅ Handle both grayscale and RGB safely
    if len(img.shape) == 3:
        gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    else:
        gray = img  # already grayscale

    # Try multiple preprocessing methods
    methods = [
        gray,
        cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)[1],
        cv2.adaptiveThreshold(
            gray, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, 11, 2
        )
    ]

    for m in methods:
        data, _, _ = detector.detectAndDecode(m)
        if data:
            return data

    return None

# ---------------- ENCODE ---------------- #
if st.session_state.mode == "Encode":

    st.markdown("### Enter data to encode")
    text = st.text_area("")

    MAX_TOTAL = 2953 * 3

    if text:
        usage = min(len(text.encode()) / MAX_TOTAL, 1.0)
        st.markdown(f"Capacity used: {int(usage * 100)}%")
        st.progress(usage)

    if st.button("Generate QR", type="primary"):
        if text:
            try:
                with st.spinner("Generating RGB QR..."):

                    compressed = zlib.compress(text.encode())
                    encrypted = encrypt_data(compressed, key)
                    b64 = base64.b64encode(encrypted).decode()

                    part_size = (len(b64) + 2) // 3

                    r_data = b64[:part_size]
                    g_data = b64[part_size:2 * part_size]
                    b_data = b64[2 * part_size:]

                    qr_r = generate_qr(r_data)
                    qr_g = generate_qr(g_data)
                    qr_b = generate_qr(b_data)

                    rgb_qr = merge_rgb(qr_r, qr_g, qr_b)

                col1, col2 = st.columns([1,1])

                with col1:
                    st.image(rgb_qr, caption="RGB QR Code", width=260)

                with col2:
                    st.markdown("### Details")
                    st.markdown(f"Original: {len(text)} chars")
                    st.markdown(f"Compressed: {len(compressed)} bytes")
                    st.markdown(f"Encrypted: {len(encrypted)} bytes")

                buf = io.BytesIO()
                rgb_qr.save(buf, format="PNG")

                st.download_button(
                    "Download RGB QR",
                    buf.getvalue(),
                    "rgb_qr.png",
                    "image/png"
                )

                st.success("QR Generated Successfully")

            except Exception as e:
                st.error(f"Error: {e}")

# ---------------- DECODE ---------------- #
elif st.session_state.mode == "Decode":

    st.markdown("### Decode QR Code")

    option = st.radio("Choose Input Method", ["Upload Image", "Use Camera"])

    detector = cv2.QRCodeDetector()

    if option == "Upload Image":
        uploaded = st.file_uploader("Upload RGB QR", type=["png", "jpg"])

        if uploaded:
            image = Image.open(uploaded).convert("RGB")
            st.image(image, caption="Uploaded Image", width=300)

            r, g, b = split_rgb(image)

            # Debug view
            st.markdown("### Channel Debug")
            c1, c2, c3 = st.columns(3)
            c1.image(r, caption="R")
            c2.image(g, caption="G")
            c3.image(b, caption="B")

            r_data = decode_qr(r, detector)
            g_data = decode_qr(g, detector)
            b_data = decode_qr(b, detector)

            if not r_data or not g_data or not b_data:
                failed = []
                if not r_data: failed.append("R")
                if not g_data: failed.append("G")
                if not b_data: failed.append("B")
                st.error(f"Failed channels: {', '.join(failed)}")
            else:
                try:
                    full = r_data + g_data + b_data
                    encrypted = base64.b64decode(full)
                    decrypted = decrypt_data(encrypted, key)
                    original = zlib.decompress(decrypted).decode()

                    st.success("Decoded Data")
                    st.text_area("Output", original, height=150)

                except:
                    st.error("Decoding failed")

    elif option == "Use Camera":
        img_file = st.camera_input("Scan QR")

        if img_file:
            image = Image.open(img_file).convert("RGB")
            st.image(image, caption="Captured Image", width=300)

            r, g, b = split_rgb(image)

            r_data = decode_qr(r, detector)
            g_data = decode_qr(g, detector)
            b_data = decode_qr(b, detector)

            if not r_data or not g_data or not b_data:
                failed = []
                if not r_data: failed.append("R")
                if not g_data: failed.append("G")
                if not b_data: failed.append("B")
                st.warning(f"Try better lighting. Failed: {', '.join(failed)}")
            else:
                try:
                    full = r_data + g_data + b_data
                    encrypted = base64.b64decode(full)
                    decrypted = decrypt_data(encrypted, key)
                    original = zlib.decompress(decrypted).decode()

                    st.success("Decoded Data")
                    st.text_area("Output", original, height=150)

                except:
                    st.error("Decoding failed")

# ---------------- FOOTER ---------------- #
st.markdown("---")
st.markdown("<p style='text-align: center;'>Streamlit RGB QR System</p>", unsafe_allow_html=True)