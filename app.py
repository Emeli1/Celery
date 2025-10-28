from flask import Flask, request, jsonify, send_file
from celery import Celery
import io
from upscale import upscale
import redis

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'files'
celery_app = Celery(
    app.name,
    backend='redis://localhost:6379/0',
    broker='redis://localhost:6379/0',
)
celery_app.conf.update(app.config)

r = redis.Redis(host='localhost', port=6379, db=1)

tasks = {}   # task_id: {'status': 'pending', 'file': '...' }

@celery_app.task(bind=True)
def upscale_image(self, image_data):
    processed_image = upscale(image_data)
    task_id = self.request.id
    r.setex(f'image:{task_id}', 3600, processed_image)  # Сохраняем в Redis
    return "Done"

def get_processed_file(task_id):
    image_data = r.get(f'image:{task_id}') # Получаем из Redis
    if image_data:
        return send_file(io.BytesIO(image_data), mimetype='image/png')

@app.route('/upscale', methods=['POST'])
def upscale_route():
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    # Проверка типа файла
    allowed_extensions = {'png', 'jpg', 'jpeg'}
    if not('.' in file.filename and file.filename.rsplit('.', 1)[1].lower() in allowed_extensions):
        return jsonify({"error": "Unsupported file type"}), 400

    image_data = file.read()
    task = upscale_image.apply_async(args=[image_data])
    return jsonify({"task_id": task.id}), 202

@app.route('/tasks/<task_id>', methods=['GET'])
def get_task_status(task_id):
    task = upscale_image.AsyncResult(task_id)
    if task.state == 'FAILURE':
        return jsonify({"status": "failed"}), 200
    elif task.state == 'SUCCESS':
        return jsonify({"status": "completed", "file": f'/processed/{task_id}'}), 200
    else:
        return jsonify({"status": "pending"}), 200

@app.route('/processed/<task_id>', methods=['GET'])
def get_processed_file(task_id):
    image_data = r.get(f'image:{task_id}')  # Получаем изображение из Redis
    if image_data:
        return send_file(io.BytesIO(image_data), mimetype='image/png')
    return jsonify({"error": "File not found"}), 404

if __name__ == '__main__':
    app.run(debug=True)


