import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import sqlite3

DB_FILE = "benchmark.db"

def get_average_metrics():
    with sqlite3.connect(DB_FILE) as conn:
        cur = conn.cursor()
        cur.execute('''SELECT 
            AVG(cpu_usage), AVG(gpu_usage), AVG(ram_used), AVG(vram_used),
            AVG(accuracy), AVG(inference_time) FROM benchmarks''')
        row = cur.fetchone()
    return {
        'cpu': row[0] or 0, 'gpu': row[1] or 0, 'ram': row[2] or 0,
        'vram': row[3] or 0, 'accuracy': row[4] or 0, 'inference_time': row[5] or 0
    }

def create_model_chart_folder(base_dir, model_name):
    model_folder = os.path.join(base_dir, os.path.splitext(model_name)[0])
    os.makedirs(model_folder, exist_ok=True)
    return model_folder

def generate_individual_charts(metrics, model_name, base_folder):
    avg = get_average_metrics()
    model_folder = create_model_chart_folder(base_folder, model_name)
    chart_paths = {}

    metric_labels = {
        'cpu': 'CPU Usage',
        'gpu': 'GPU Usage',
        'ram': 'RAM Usage (MB)',
        'vram': 'VRAM Usage (MB)',
        'accuracy': 'Accuracy (%)',
        'inference_time': 'Inference Time (s)'
    }

    for key, label in metric_labels.items():
        current = metrics[key]
        average = avg.get(key, 0)

        fig, ax = plt.subplots(figsize=(5, 4))
        fig.patch.set_facecolor('#0c0c0e')
        ax.set_facecolor('#0c0c0e')

        bars = ax.bar(['Current', 'Average'], [current, average], color=['skyblue', 'lightcoral'])
        ax.set_title(f'{label} Comparison', color='white')
        ax.set_ylabel(label, color='white')
        ax.tick_params(colors='white')

        for spine in ax.spines.values():
            spine.set_edgecolor('white')

        for bar in bars:
            bar.set_edgecolor('white')

        plt.tight_layout()

        chart_filename = f'{key}.png'
        chart_path = os.path.join(model_folder, chart_filename)
        plt.savefig(chart_path, facecolor=fig.get_facecolor())
        plt.close()

        chart_paths[key] = chart_path

    return chart_paths
