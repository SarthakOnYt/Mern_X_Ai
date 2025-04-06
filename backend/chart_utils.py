import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from benchmark_utils import get_average_metrics

def create_model_chart_folder(base_dir, model_name):
    folder = os.path.join(base_dir, model_name)
    os.makedirs(folder, exist_ok=True)
    return folder

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

        plt.figure(figsize=(5, 4))
        plt.bar(['Current', 'Average'], [current, average], color=['skyblue', 'lightcoral'])
        plt.title(f'{label} Comparison')
        plt.ylabel(label)
        plt.tight_layout()

        chart_filename = f'{key}.png'
        chart_path = os.path.join(model_folder, chart_filename)
        plt.savefig(chart_path)
        plt.close()

        chart_paths[key] = chart_path

    return chart_paths
