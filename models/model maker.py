import torch
import torch.nn as nn

class UltraHugeModel(nn.Module):
    def __init__(self, input_size=512, hidden_size=2048, output_size=512, num_layers=200):
        super(UltraHugeModel, self).__init__()
        self.num_layers = num_layers

        self.layers = nn.ModuleList()
        self.layers.append(nn.Linear(input_size, hidden_size))

        for _ in range(num_layers - 2):
            self.layers.append(nn.Linear(hidden_size, hidden_size))

        self.layers.append(nn.Linear(hidden_size, output_size))
        self.relu = nn.ReLU()
        self.intermediate_outputs = []

    def forward(self, x):
        self.intermediate_outputs = [x]

        for layer in self.layers[:-1]:
            x = self.relu(layer(x))
            self.intermediate_outputs.append(x)

        x = self.layers[-1](x)
        return x

    def backtrack(self, layer_index):
        if 0 <= layer_index < len(self.intermediate_outputs):
            return self.intermediate_outputs[layer_index]
        else:
            raise IndexError(f"Layer index {layer_index} out of range.")

# Instantiate and test
if __name__ == "__main__":
    model = UltraHugeModel()
    dummy_input = torch.randn(1, 512)
    output = model(dummy_input)
    print("✅ Forward pass complete.")
    
    torch.save(model.state_dict(), "ultrahuge_model_200.pt")
    print("📦 Saved as 'ultrahuge_model_200.pt'")
