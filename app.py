import streamlit as st
from PIL import Image
from rgb_qr_core import generate_rgb_qr, split_and_decode_rgb_qr
import base64
from io import BytesIO

st.set_page_config(page_title="RGB_QR Web App", layout="centered")

st.title("🌈 RGB_QR Web Application")

option = st.radio("Choose Option:", ["Create QR", "Scan QR"])


# =====================================================
# CREATE QR MODE
# =====================================================

if option == "Create QR":

    st.subheader("Enter Up To Three Links or Data")

    red_link = st.text_input(
        "🔴 Red Layer (Optional)",
        value="",
        placeholder="Enter link or text..."
    )

    green_link = st.text_input(
        "🟢 Green Layer (Optional)",
        value="",
        placeholder="Enter link or text..."
    )

    blue_link = st.text_input(
        "🔵 Blue Layer (Optional)",
        value="",
        placeholder="Enter link or text..."
    )

    if st.button("Generate Combined RGB QR"):

        if not red_link and not green_link and not blue_link:
            st.warning("Please enter at least one link or data.")
        else:
            rgb_qr_image = generate_rgb_qr(
                red_link,
                green_link,
                blue_link
            )

            # Centered QR Display
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                st.image(
                    rgb_qr_image,
                    caption="Combined RGB QR",
                    width=350
                )

            # Convert image to bytes
            buffered = BytesIO()
            rgb_qr_image.save(buffered, format="PNG")
            img_bytes = buffered.getvalue()

            # Download Button
            st.download_button(
                label="⬇ Download RGB_QR",
                data=img_bytes,
                file_name="rgb_qr.png",
                mime="image/png"
            )

            # =====================================================
            # SHARE FEATURE (LONG BASE64 IMAGE LINK)
            # =====================================================

            st.markdown("### 🔗 Share QR")

            base64_img = base64.b64encode(img_bytes).decode()
            share_link = f"data:image/png;base64,{base64_img}"

            with st.expander("Click to view share link"):
                st.text_area(
                    "Copy this link:",
                    value=share_link,
                    height=150
                )

            st.success("RGB_QR Generated Successfully!")


# =====================================================
# SCAN QR MODE
# =====================================================

elif option == "Scan QR":

    st.subheader("Scan RGB_QR")

    scan_option = st.radio(
        "Choose Scan Method:",
        ["Upload Image", "Use Camera"]
    )

    image = None

    # ---------------- Upload Image ----------------
    if scan_option == "Upload Image":

        uploaded_file = st.file_uploader(
            "Upload RGB_QR Image",
            type=["png", "jpg", "jpeg"]
        )

        if uploaded_file:
            image = Image.open(uploaded_file)

    # ---------------- Camera Scan ----------------
    elif scan_option == "Use Camera":

        camera_image = st.camera_input("Take a picture of RGB_QR")

        if camera_image:
            image = Image.open(camera_image)

    # ---------------- Decode Section ----------------
    if image:

        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.image(
                image,
                caption="Scanned RGB_QR",
                width=350
            )

        if st.button("Decode RGB_QR"):
            red, green, blue = split_and_decode_rgb_qr(image)

            st.success("Decoding Completed")

            st.markdown("### 🔓 Recovered Data")

            st.write("🔴 Red Layer:", red if red else "Empty")
            st.write("🟢 Green Layer:", green if green else "Empty")
            st.write("🔵 Blue Layer:", blue if blue else "Empty")
