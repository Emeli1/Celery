from flask import Flask, request, jsonify, send_file
import celery
import io
from upscale import upscale

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'files'
celery = celery.Celery(app.name,
    backend='redis://localhost:6379/0',
    broker='redis://localhost:6379/0',
)
celery.conf.update(app.config)

tasks = {}

@celery.task(bind=True)
def upscale_image(self, image_data):
    processed_image = upscale(image_data)
    task_id = self.request.id
    tasks[task_id] = processed_image
    return "Done"

@app.route('/app', methods=['POST'])
def upscale_route():
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files["file"]

    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    image_data = file.read()
    task = upscale_image.apply_async(args=[image_data])
    return jsonify({"task_id": task.id}), 202

@app.route('/tasks/<task_id>', methods=['GET'])
def get_task_status(task_id):
    if task_id in tasks:
        return jsonify({"status:": "completed", "file": f'/processed/{task_id}'}), 200
    else:
        task = upscale_image.AsyncResult(task_id)
        status = "PENDING"
        if task.state == "FAILURE":
            status = "failed"
        elif task.state == "SUCCESS":
            status = "completed"
        return jsonify({"status": status}), 200

@app.route('/processed/<task_id>', methods=['GET'])
def get_processed_file(task_id):
    if task_id in tasks:
        image_data = tasks[task_id]
        return send_file(io.BytesIO(image_data), mimetype='image/png')
    return jsonify({"error": "File not found"}), 404

if __name__ == '__main__':
    app.run(debug=True)


