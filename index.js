const modelInput = document.getElementById("modelFile");
const datasetSelect = document.getElementById("datasetSelect");
const submitButton = document.getElementById("submitBtn");
const outputDiv = document.getElementById("outputData");
const server_link = "http://localhost:5000"; // Backend Flask server

// Prevent multiple event listeners
if (!submitButton.hasAttribute("data-bound")) {
    submitButton.setAttribute("data-bound", "true");

    submitButton.addEventListener("click", async (e) => {
        e.preventDefault();

        const modelFile = modelInput.files[0];
        const dataset = datasetSelect.value;
        const user_id = "user123"; // Replace with dynamic user input if needed

        if (!modelFile || !dataset) {
            alert("Please select both a model file and a dataset.");
            return;
        }

        const formData = new FormData();
        formData.append("model", modelFile);
        formData.append("dataset_name", dataset);
        formData.append("user_id", user_id);

        try {
            const response = await fetch(`${server_link}/upload`, {
                method: "POST",
                body: formData,
            });

            const result = await response.json();
            console.log("🔍 Full server response:", result);

            if (result.metrics) {
                const benchmark = result.metrics;

                console.log("✅ Benchmark Results:");
                console.table({
                    Model: modelFile.name,
                    Dataset: dataset,
                    CPU_Usage: benchmark.cpu,
                    RAM_Used_GB: benchmark.ram,
                    Accuracy: benchmark.accuracy,
                    Inference_Time_s: benchmark.inference_time,
                });

                let chartsHTML = "";
                if (result.charts && typeof result.charts === "object") {
                    for (const key in result.charts) {
                        if (result.charts.hasOwnProperty(key)) {
                            const chartUrl = `${server_link}${result.charts[key]}`;
                            chartsHTML += `
                                <div style="margin-bottom: 10px;">
                                    <strong>${key.replace(/_/g, ' ').toUpperCase()} Chart:</strong><br />
                                    <img src="${chartUrl}" style="max-width: 100%; border: 1px solid #ccc;" />
                                </div>
                            `;
                        }
                    }
                }

                // PDF report button
                let pdfHTML = "";
                if (result.pdf_report) {
                    const pdfUrl = `${server_link}${result.pdf_report}`;
                    pdfHTML = `
                        <div style="margin-top: 20px;">
                            <a href="${pdfUrl}" target="_blank" class="btn btn-primary">
                                📄 Download PDF Report
                            </a>
                        </div>
                    `;
                }

                outputDiv.innerHTML = `
                    <h2>Benchmark Summary</h2>
                    <div class="summary-grid">
                        <div><strong>Model:</strong> ${modelFile.name}</div>
                        <div><strong>Dataset:</strong> ${dataset}</div>
                        <div><strong>POINTS:</strong> ${benchmark.benchmark_points}</div>
                        <div><strong>CPU:</strong> ${benchmark.cpu}</div>
                        <div><strong>RAM:</strong> ${benchmark.ram} GB</div>
                        <div><strong>GPU:</strong> ${benchmark.gpu}</div>
                        <div><strong>VRAM:</strong> ${benchmark.vram} GB</div>
                        <div><strong>Accuracy:</strong> ${benchmark.accuracy}%</div>
                        <div><strong>Inference Time:</strong> ${benchmark.inference_time} s</div>
                    </div>
                    <h3>Charts:</h3>
                    ${chartsHTML}
                    ${pdfHTML}
                `;
            } else {
                console.warn("⚠️ Server responded with error:", result.error);
                outputDiv.innerHTML = `<p class="error">Error: ${result.error}</p>`;
            }
        } catch (err) {
            console.error("❌ Request failed:", err);
            outputDiv.innerHTML = `<p class="error">Failed to connect to backend</p>`;
        }
    });
}
