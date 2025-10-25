import pytest
import io
from app import app, celery, upscale_image

@pytest.fixture
def client():
    """Настраиваем тестовый клиент Flask."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_upscale_route(client):
    """Тестируем эндпоинт загрузки изображения и получения task_id.
    Важно: файл 'lama_300px.png' должен существовать в директории с тестами."""

    try:
        with open('lama_300px.png', 'rb') as img: # Открываем тестовый файл
            image_data = img.read() #Читаем содержимое файла
            data = {'file': (io.BytesIO(image_data), 'lama_300px.png')} #Создаем данные для отправки POST запроса
            response = client.post('/app', content_type='multipart/form-data', data=data) #Выполняем POST запрос

        # Проверяем успешность запроса и наличие task_id
        assert response.status_code == 202 #Проверяем код ответа
        json_data = response.get_json() #Получаем json из ответа
        assert 'task_id' in json_data #Проверяем наличие task_id
    except FileNotFoundError:
        pytest.fail("Не найден файл lama_300px.png.  Убедитесь, что он находится в той же директории, что и тест.")

def test_get_task_status(client):
    """Тестируем получение статуса задачи по task_id. Требует предварительной отправки файла."""
    # Отправляем POST-запрос для создания задачи
    try:
        with open('lama_300px.png', 'rb') as img:
            image_data = img.read()
            data = {'file': (io.BytesIO(image_data), 'lama_300px.png')}
            response = client.post('/app', content_type='multipart/form-data', data=data)

        task_id = response.get_json()['task_id']

        # Получаем статус задачи
        response = client.get(f'/tasks/{task_id}')
        assert response.status_code == 200
        assert response.get_json()['status'] in ['PENDING', 'completed']
    except FileNotFoundError:
        pytest.fail("Не найден файл")