import cv2
from cv2 import dnn_superres
import numpy as np


# Глобальная переменная для модели
scaler = None


def load_model(model_path: str):
    global scaler
    if scaler is None:
        scaler = dnn_superres.DnnSuperResImpl_create()
        scaler.readModel(model_path)
        scaler.setModel("edsr", 2)

def upscale(image_data: bytes) -> bytes:
    """
    :param image_data: бинарные данные изображения для апскейла
    :return: бинарные данные обработанного изображения
    """
    load_model("EDSR_x2.pb")

    image_array = np.frombuffer(image_data, np.uint8)
    image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

    result = scaler.upsample(image)
    _, encoded_image = cv2.imencode(".png", result)
    return encoded_image.tobytes()


def example():
    upscale('lama_300px.png', 'lama_600px.png')


if __name__ == '__main__':
    example()