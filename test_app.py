import os

import pytest
import io
from app import app, celery_app
import time
from app import app


@pytest.fixture
def client():
    """Настраиваем тестовый клиент Flask."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@pytest.fixture
def image_data():
    """Фикстура для чтения данных изображения из файла."""
    image_path = 'lama_300px.png'
    if not os.path.exists(image_path):
        pytest.skip(f"Файл {image_path} не найден, пропускаем тест.")
    with open(image_path, 'rb') as img:
        return img.read()

def test_upscale_route(client, image_data):
    """Тестируем эндпоинт загрузки изображения и получения task_id."""
    data = {'file': (io.BytesIO(image_data), 'lama_300px.png')}
    response = client.post('/upscale', content_type='multipart/form-data', data=data)
    assert response.status_code == 202
    assert 'task_id' in response.get_json()

def test_get_task_status(client):
    """Тестируем получение статуса задачи по task_id."""
    data = {'file': (io.BytesIO(b'test image data'), 'lama_300px.png')}
    response = client.post('/upscale', content_type='multipart/form-data', data=data)
    task_id = response.get_json()['task_id']
    response = client.get(f'/tasks/{task_id}')
    assert response.status_code == 200
    assert response.get_json()['status'].lower() in ['pending', 'failed']

def test_get_status_invalid_task(client):
    """Тестируем получение статуса задачи с несуществующим task_id."""
    invalid_task_id = 'nonexistenttaskid123'
    response = client.get(f'/tasks/{invalid_task_id}')
    assert response.status_code == 200
    assert response.get_json()['status'].lower() in ['pending', 'failed']


def test_processed_file(client):
    """Тестируем получение обработанного файла по task_id."""
    image_data = b'test image data'
    data = {'file': (io.BytesIO(image_data), 'lama_300px.png')}
    response = client.post('/upscale', content_type='multipart/form-data', data=data)
    task_id = response.get_json()['task_id']
    time.sleep(5)
    response = client.get(f'/processed/{task_id}')
    if response.status_code == 200:
        assert response.mimetype == 'image/png'
    else:
        assert response.status_code == 404


def test_no_file_upload(client):
    """Тестируем эндпоинт загрузки изображения без файла."""
    response = client.post('/upscale', content_type='multipart/form-data', data={})
    assert response.status_code == 400
    assert response.get_json()['error'] == 'No file part'