// Create particles
const particlesContainer = document.getElementById('particles');
const particleCount = 30;

for (let i = 0; i < particleCount; i++) {
    const particle = document.createElement('div');
    particle.classList.add('particle');
    
    // Random position
    particle.style.left = Math.random() * 100 + '%';
    particle.style.top = Math.random() * 100 + '%';
    
    // Random size
    const size = Math.random() * 4 + 1;
    particle.style.width = size + 'px';
    particle.style.height = size + 'px';
    
    // Random opacity
    particle.style.opacity = Math.random() * 0.5 + 0.1;
    
    // Animation
    particle.style.animation = `float ${Math.random() * 15 + 10}s ease-in-out infinite`;
    particle.style.animationDelay = `${Math.random() * 5}s`;
    
    particlesContainer.appendChild(particle);
}

// Smooth scroll to input section when Get Started is clicked
document.getElementById('get-started-btn').addEventListener('click', function(e) {
    e.preventDefault();
    document.getElementById('input-section').scrollIntoView({ 
        behavior: 'smooth' 
    });
});

// Display file name when file is selected
document.getElementById('modelFile').addEventListener('change', function() {
    const fileName = this.files[0] ? this.files[0].name : 'No file chosen';
    document.getElementById('file-name-display').textContent = fileName;
});

// Header scroll effect
window.addEventListener('scroll', function() {
    const header = document.getElementById('header');
    if (window.scrollY > 50) {
        header.classList.add('header-scrolled');
    } else {
        header.classList.remove('header-scrolled');
    }
});

// Show input section with animation when scrolled to
const inputSection = document.getElementById('input-section');
const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.classList.add('visible');
        }
    });
}, { threshold: 0.2 });

observer.observe(inputSection);



// BACKEND CONNECTOR DO NOT TOUCH
const modelInput = document.getElementById("modelFile");
const datasetSelect = document.getElementById("datasetSelect");
const submitButton = document.getElementById("submitBtn");
const outputDiv = document.getElementById("outputData");
const server_link = "https://publisher-hybrid.gl.at.ply.gg:15929/"; // Backend Flask server

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