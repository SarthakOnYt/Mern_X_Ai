import os
import gc
import time
import torch
import sqlite3
import threading
import pandas as pd
import torch.nn as nn
import GPUtil
import psutil
from flask import Flask, request, jsonify, send_from_directory,send_file
from flask_cors import CORS
from chart_generator import generate_individual_charts
from generate_pdf import generate_pdf

# ---------- Config ----------
UPLOAD_FOLDER = 'uploads'
DATASET_FOLDER = 'datasets'
CHART_FOLDER = os.path.abspath("charts")

DB_FILE = 'benchmark.db'
EXPIRY_SECONDS = 600  # 10 minutes

app = Flask(__name__)
CORS(app)

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(DATASET_FOLDER, exist_ok=True)
os.makedirs(CHART_FOLDER, exist_ok=True)

# ---------- Database ----------
def init_db():
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS benchmarks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            model_name TEXT,
            cpu_usage REAL,
            gpu_usage REAL,
            ram_used REAL,
            vram_used REAL,
            accuracy REAL,
            inference_time REAL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )''')

def save_to_db(user_id, model_name, metrics):
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute('''INSERT INTO benchmarks 
        (user_id, model_name, cpu_usage, gpu_usage, ram_used, vram_used, accuracy, inference_time)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
        (user_id, model_name, metrics['cpu'], metrics['gpu'], metrics['ram'],
         metrics['vram'], metrics['accuracy'], metrics['inference_time']))
        conn.commit()

# ---------- Helpers ----------
def cleanup(*objs):
    for obj in objs:
        if isinstance(obj, torch.nn.Module):
            for param in obj.parameters():
                param.detach_()
        del obj
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        torch.cuda.ipc_collect()

def delete_file_after_delay(path, delay):
    def _delete():
        time.sleep(delay)
        if os.path.exists(path):
            os.remove(path)
        # Also delete charts folder
        model_name = os.path.splitext(os.path.basename(path))[0]
        chart_dir = os.path.join(CHART_FOLDER, model_name)
        if os.path.exists(chart_dir):
            import shutil
            shutil.rmtree(chart_dir, ignore_errors=True)
    threading.Thread(target=_delete, daemon=True).start()

def load_chatbot_csv(path):
    df = pd.read_csv(path)
    return df['input'].tolist(), df['output'].tolist()

def benchmark_model(model_path, inputs, outputs):
    start = time.time()
    loaded = torch.load(model_path, map_location=torch.device('cpu'))
    state_dict = None
    model = None
    dummy_input = None

    try:
        if isinstance(loaded, nn.Module):
            model = loaded
        elif isinstance(loaded, dict):
            state_dict = loaded
        else:
            raise ValueError("Invalid model format")

        if state_dict:
            layers = []
            layer_keys = sorted([k for k in state_dict if 'weight' in k and len(state_dict[k].shape) == 2])
            for i, weight_key in enumerate(layer_keys):
                out_features, in_features = state_dict[weight_key].shape
                layers.append(nn.Linear(in_features, out_features))
            model = nn.Sequential(*layers)
            model.load_state_dict(state_dict, strict=False)

        model.eval()
        process = psutil.Process(os.getpid())
        ram_before = process.memory_info().rss
        cpu_start = time.process_time()

        dummy_input = torch.randn(1, model[0].in_features)
        with torch.no_grad():
            model(dummy_input)

        cpu_end = time.process_time()
        ram_after = process.memory_info().rss
        ram_used = round((ram_after - ram_before) / 1e6, 2)
        cpu_time = round(cpu_end - cpu_start, 4)

        correct = sum(1 for i in range(min(len(inputs), 10)) if inputs[i] == outputs[i])
        accuracy = (correct / 10) * 100
        duration = round(time.time() - start, 2)

        try:
            gpus = GPUtil.getGPUs()
            gpu_util = round(gpus[0].load * 100, 2) if gpus else 0
            vram_used = round(gpus[0].memoryUsed / 1024, 2) if gpus else 0
        except:
            gpu_util, vram_used = 0, 0

        # --- Benchmark Points Calculation ---
        baseline = {
            'cpu': 2.0,
            'gpu': 100.0,
            'ram': 1000.0,
            'vram': 4.0,
            'accuracy': 100.0,
            'inference_time': 5.0
        }

        weights = {
            'cpu': 0.15,
            'gpu': 0.15,
            'ram': 0.15,
            'vram': 0.10,
            'accuracy': 0.35,
            'inference_time': 0.10
        }

        score_cpu = max(0, (1 - (cpu_time / baseline['cpu'])) * weights['cpu'] * 100)
        score_gpu = min((gpu_util / baseline['gpu']) * weights['gpu'] * 100, weights['gpu'] * 100)
        score_ram = max(0, (1 - (ram_used / baseline['ram'])) * weights['ram'] * 100)
        score_vram = max(0, (1 - (vram_used / baseline['vram'])) * weights['vram'] * 100)
        score_accuracy = min((accuracy / baseline['accuracy']) * weights['accuracy'] * 100, weights['accuracy'] * 100)
        score_infer = max(0, (1 - (duration / baseline['inference_time'])) * weights['inference_time'] * 100)

        points = round(score_cpu + score_gpu + score_ram + score_vram + score_accuracy + score_infer, 2)

        return {
            'benchmark_points': points,
            'cpu': cpu_time,
            'gpu': gpu_util,
            'ram': ram_used,
            'vram': vram_used,
            'accuracy': round(accuracy, 2),
            'inference_time': duration
        }

    finally:
        cleanup(model, dummy_input, loaded, state_dict)

@app.route('/charts/<model>/<filename>')
def serve_chart(model, filename):
    chart_dir = os.path.join(CHART_FOLDER, model)
    chart_path = os.path.join(chart_dir, filename)

    if not os.path.exists(chart_path):
        return jsonify({'error': 'Chart not found'}), 404

    print(f"Serving chart from {chart_path}")
    return send_from_directory(chart_dir, filename)

@app.route('/report/<filename>')
def serve_report(filename):
    report_path = os.path.join("pdf_reports", filename)
    if os.path.exists(report_path):
        return send_file(report_path, as_attachment=True)
    return jsonify({'error': 'PDF report not found'}), 404

# ---------- Routes ----------
@app.route('/upload', methods=['POST'])
def upload():
    user_id = request.form.get('user_id')
    dataset_name = request.form.get('dataset_name')
    file = request.files.get('model')

    if not file or not user_id or not dataset_name:
        return jsonify({'error': 'Missing required fields'}), 400
    if not file.filename.endswith('.pt'):
        return jsonify({'error': 'Only .pt files supported'}), 400

    dataset_path = os.path.join(DATASET_FOLDER, dataset_name)
    if not os.path.exists(dataset_path):
        return jsonify({'error': 'Dataset not found'}), 404

    model_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(model_path)
    delete_file_after_delay(model_path, EXPIRY_SECONDS)

    try:
        inputs, outputs = load_chatbot_csv(dataset_path)
        metrics = benchmark_model(model_path, inputs, outputs)
        save_to_db(user_id, file.filename, metrics)
        chart_paths = generate_individual_charts(metrics, file.filename, CHART_FOLDER)

        # Convert paths for frontend
        model_folder = file.filename.split('.')[0]
        chart_urls = {
            k: f"/charts/{model_folder}/{os.path.basename(v)}"
            for k, v in chart_paths.items()
        }

        # Generate PDF report
        pdf_output_path = os.path.join("pdf_reports", f"{model_folder}_report.pdf")
        os.makedirs("pdf_reports", exist_ok=True)
        generate_pdf(metrics, chart_paths, model_name=model_folder, output_path=pdf_output_path)

        return jsonify({
            'success': True,
            'metrics': metrics,
            'charts': chart_urls,
            'pdf_report': f"/report/{model_folder}_report.pdf"
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500




# ---------- Main ----------
if __name__ == '__main__':
    init_db()
    app.run(debug=True)
