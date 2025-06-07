import base64
import io
import numpy as np
import Preprocessor
from PIL import Image
import onnxruntime as ort

# Load ONNX model
onnx_model_path = './model/dfd_p1.onnx'
session = ort.InferenceSession(onnx_model_path)
input_name = session.get_inputs()[0].name

# Preprocessing base64 image
def preprocess_base64_image(base64_string):
    try:
        if not base64_string.startswith("data:image"):
            return None

        _, base64_data = base64_string.split(",", 1)
        image_data = base64.b64decode(base64_data)
        image = Image.open(io.BytesIO(image_data)).convert("RGB")

        # Resize and normalize manually
        image = image.resize((128, 128))
        img_array = np.array(image).astype(np.float32) / 255.0
        img_array = (img_array - 0.5) / 0.5  # Normalize like PyTorch

        # Convert to NCHW (1, 3, 128, 128)
        img_array = np.transpose(img_array, (2, 0, 1))
        img_array = np.expand_dims(img_array, axis=0)
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
        prediction = float(output[0][0])

        label = 'Real' if prediction > 0.5 else 'Fake'
        accuracy = round(prediction * 100, 2) if label == 'Real' else round((1 - prediction) * 100, 2)
        accuracy = 99.98 if accuracy == 100 else accuracy

        return {"class": label, "accuracy": accuracy}
    except Exception as e:
        return {"error": str(e)}

def detect_image(input_list, heatmap):
    image_path = str(input_list[0])
    extension = str(input_list[1])
    new_image_path = None

    # print(f"image load: {image_path}")
    if(image_path=='load'):
        image_path = Preprocessor.Tools.merge_list_to_string(Preprocessor.single_img_bin.copy())

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