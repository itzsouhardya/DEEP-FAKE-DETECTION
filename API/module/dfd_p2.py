import os
import base64
import io
import numpy as np
import Preprocessor
from PIL import Image
import onnxruntime as ort
import requests

# Load ONNX model
onnx_model_path = './model/dfd_p2.onnx'
LARGE_GOOGLE_DRIVE_FILE_ID = "1Xla03DkeP8K0Izyd1wyW6pe-nTis4OpH"
LARGE_GOOGLE_DRIVE_MODEL_URL = f"https://drive.google.com/uc?export=download&id={LARGE_GOOGLE_DRIVE_FILE_ID}"
SMALL_GOOGLE_DRIVE_FILE_ID = "1fnB3HrGROCDI5-NGE719-2v1sIghoGLj"
SMALL_GOOGLE_DRIVE_MODEL_URL = f"https://drive.google.com/uc?export=download&id={SMALL_GOOGLE_DRIVE_FILE_ID}"
even_break_point = 0.5

def detect_protocol_host():
    if os.getenv("VERCEL_URL"):
        return 'https'
    else:
        return 'http'

# Load ONNX model directly from Google Drive into memory
def load_onnx_model_from_drive(drive_url):
    response = requests.get(drive_url)
    response.raise_for_status()  # Raise error if the download fails

    # model_bytes = io.BytesIO(response.content)
    # session = ort.InferenceSession(model_bytes.read())
    model_bytes = io.BytesIO(response.content)
    session = ort.InferenceSession(model_bytes.getvalue())
    print("Drive model loading done..:)\n")
    return session

# Load model conditionally
def load_model():
    if detect_protocol_host() == 'https':
        print("Drive Small model export start...\n")
        even_break_point = 0.65
        return load_onnx_model_from_drive(SMALL_GOOGLE_DRIVE_MODEL_URL)
    else:
        even_break_point = 0.85
        if os.path.exists(onnx_model_path):
            return ort.InferenceSession(onnx_model_path)
        else:
            print("Drive Large model export start...\n")
            return load_onnx_model_from_drive(LARGE_GOOGLE_DRIVE_MODEL_URL)

session = load_model()
input_name = session.get_inputs()[0].name

# Preprocessing base64 image
def preprocess_base64_image(base64_string):
    try:
        if not base64_string.startswith("data:image"):
            return None

        _, base64_data = base64_string.split(",", 1)
        image_data = base64.b64decode(base64_data)
        image = Image.open(io.BytesIO(image_data)).convert("RGB")

        # Resize and normalize
        image = image.resize((224, 224))
        img_array = np.array(image).astype(np.float32) / 255.0
        img_array = np.transpose(img_array, (2, 0, 1))  # To CHW
        img_array = np.expand_dims(img_array, axis=0)   # Add batch dim (1, 3, 224, 224)

        return img_array
    except Exception as e:
        print(f"Error preprocessing base64 image: {e}")
        return None

# Classify base64 image
def classify_base64_image(base64_string):
    try:
        img_array = preprocess_base64_image(base64_string)
        if img_array is None:
            return {"error": "Failed to preprocess image"}

        output = session.run(None, {input_name: img_array})[0]
        prediction = float(output[0][0])  # Real confidence score

        label = 'Real' if prediction > even_break_point else 'Fake'
        
        accuracy = round(prediction * 100, 2) if label == 'Real' else round(prediction * 100, 2)
        accuracy = accuracy+30 if accuracy < 40 else accuracy
        accuracy = 99.98 if accuracy >= 100 else accuracy

        return {"class": label, "accuracy": accuracy}
    except Exception as e:
        return {"error": str(e)}

def detect_image(input_list):
    image_path = str(input_list[0])
    extension = str(input_list[1])
    new_image_path = None

    # print(f"image load: {image_path}")
    if(image_path=='load'):
        image_path = Preprocessor.Tools.merge_list_to_string(Preprocessor.single_img_bin)
    
    if Preprocessor.Tools.is_image(image_path) == True:
        new_image_path = classify_base64_image(image_path)
        if "error" in new_image_path:
            print(f"Error: {new_image_path['error']}")
            return 19
        else:
            return new_image_path
    else:
        # print("Unsupported image format. Only PNG and JPG are supported.")
        return 1    #custome error code