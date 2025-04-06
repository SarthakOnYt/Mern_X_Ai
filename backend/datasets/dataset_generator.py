from datasets import load_dataset
import pandas as pd

# Load first 100 conversations
dataset = load_dataset("daily_dialog", split="train[:2000]",trust_remote_code=True)

# Extract input-output pairs from dialogues
input_texts = []
output_texts = []

for dialog in dataset['dialog']:
    for i in range(len(dialog) - 1):
        input_texts.append(dialog[i])
        output_texts.append(dialog[i + 1])

# Create DataFrame and save
df = pd.DataFrame({'input': input_texts, 'output': output_texts})
df.to_csv("Daily_dialog_2000.csv", index=False)
