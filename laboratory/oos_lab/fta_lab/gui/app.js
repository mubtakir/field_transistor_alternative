// Global Chart Instance
let ivChart = null;

document.addEventListener('DOMContentLoaded', () => {
    initSliders();
    initChart();
});

function initSliders() {
    const sliders = ['len', 'gap'];
    sliders.forEach(s => {
        const slider = document.getElementById(`${s}-slider`);
        const val = document.getElementById(`${s}-val`);
        slider.addEventListener('input', () => {
            val.textContent = slider.value;
        });
    });
}

function initChart() {
    const ctx = document.getElementById('iv-chart').getContext('2d');
    ivChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Drain Current (mA)',
                data: [],
                borderColor: '#58a6ff',
                backgroundColor: 'rgba(88, 166, 255, 0.1)',
                borderWidth: 2,
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: { 
                    title: { display: true, text: 'Gate Voltage (V)', color: '#8b949e' },
                    grid: { color: 'rgba(139, 148, 158, 0.1)' }
                },
                y: { 
                    title: { display: true, text: 'Id (mA)', color: '#8b949e' },
                    grid: { color: 'rgba(139, 148, 158, 0.1)' }
                }
            },
            plugins: {
                legend: { labels: { color: '#c9d1d9' } }
            }
        }
    });
}

document.getElementById('run-btn').addEventListener('click', async () => {
    const btn = document.getElementById('run-btn');
    btn.textContent = 'جاري المحاكاة...';
    btn.disabled = true;

    const payload = {
        device_type: "u_plate",
        geometry: {
            length: parseFloat(document.getElementById('len-slider').value) * 1e-6,
            width: 10e-6,
            gap: parseFloat(document.getElementById('gap-slider').value) * 1e-9,
            eps_r: 4.0
        },
        v_dd: parseFloat(document.getElementById('vdd-input').value),
        v_gate_range: [0.0, 10.0, 30]
    };

    try {
        const response = await fetch('/api/simulate/iv', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        
        const data = await response.json();
        updateChart(data);
    } catch (e) {
        console.error("Simulation failed:", e);
        alert("فشلت المحاكاة. تأكد من تشغيل الخادم.");
    } finally {
        btn.textContent = 'تشغيل المحاكاة';
        btn.disabled = false;
    }
});

function updateChart(data) {
    ivChart.data.labels = data.vg.map(v => v.toFixed(1));
    ivChart.data.datasets[0].data = data.id.map(i => i * 1000); // to mA
    ivChart.update();
}
