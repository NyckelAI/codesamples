from PIL import Image
from io import BytesIO
import base64


def strip_base64_prefix(inline_data: str) -> str:
    return inline_data.split(";base64,")[1]


def load_image(inline_data: str = None) -> Image:

    image_b64_encoded_string = strip_base64_prefix(inline_data)
    im_bytes = base64.b64decode(image_b64_encoded_string)
    im_file = BytesIO(im_bytes)
    img = Image.open(im_file).convert("RGB")

    return img
