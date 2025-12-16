// ===== CHART CONFIGURATION =====
let sentimentChart = null;
let wordChart = null;
let confidenceChart = null;

// Common chart options
const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
        legend: {
            position: 'bottom',
            labels: {
                padding: 20,
                usePointStyle: true,
                font: {
                    size: 12
                }
            }
        },
        tooltip: {
            backgroundColor: 'rgba(0, 0, 0, 0.8)',
            titleFont: { size: 14 },
            bodyFont: { size: 12 },
            padding: 12,
            cornerRadius: 6
        }
    }
};

// ===== SENTIMENT CHART =====
function createSentimentChart(chartData) {
    const ctx = document.getElementById('sentimentChart');
    if (!ctx) return;
    
    // Destroy existing chart
    if (sentimentChart) {
        sentimentChart.destroy();
    }
    
    sentimentChart = new Chart(ctx, {
        type: 'doughnut',
        data: chartData,
        options: {
            ...chartOptions,
            cutout: '60%',
            plugins: {
                ...chartOptions.plugins,
                tooltip: {
                    ...chartOptions.plugins.tooltip,
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = context.raw || 0;
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = Math.round((value / total) * 100);
                            return `${label}: ${value} ulasan (${percentage}%)`;
                        }
                    }
                }
            }
        }
    });
}

// ===== WORD FREQUENCY CHART =====
function createWordChart(wordData) {
    const ctx = document.getElementById('wordChart');
    if (!ctx) return;
    
    // Destroy existing chart
    if (wordChart) {
        wordChart.destroy();
    }
    
    wordChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: wordData.labels,
            datasets: [{
                label: 'Frekuensi Kata',
                data: wordData.data,
                backgroundColor: wordData.colors,
                borderColor: 'rgba(102, 126, 234, 1)',
                borderWidth: 1
            }]
        },
        options: {
            ...chartOptions,
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Jumlah Kemunculan'
                    },
                    ticks: {
                        stepSize: 1
                    }
                },
                x: {
                    ticks: {
                        maxRotation: 45,
                        minRotation: 45
                    }
                }
            },
            plugins: {
                ...chartOptions.plugins,
                legend: {
                    display: false
                }
            }
        }
    });
}

// ===== CONFIDENCE CHART =====
function createConfidenceChart(confidenceData) {
    const ctx = document.getElementById('confidenceChart');
    if (!ctx) return;
    
    // Destroy existing chart
    if (confidenceChart) {
        confidenceChart.destroy();
    }
    
    confidenceChart = new Chart(ctx, {
        type: 'line',
        data: confidenceData,
        options: {
            ...chartOptions,
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,
                    title: {
                        display: true,
                        text: 'Tingkat Kepercayaan (%)'
                    }
                }
            },
            plugins: {
                ...chartOptions.plugins,
                tooltip: {
                    ...chartOptions.plugins.tooltip,
                    callbacks: {
                        label: function(context) {
                            return `${context.dataset.label}: ${context.raw}%`;
                        }
                    }
                }
            }
        }
    });
}

// ===== UPDATE PROGRESS BARS =====
function updateProgressBars(percentages) {
    const progressBars = document.getElementById('progressBars');
    if (!progressBars) return;
    
    const colors = {
        'positif': 'positive',
        'negatif': 'negative',
        'netral': 'neutral'
    };
    
    let html = '';
    Object.entries(percentages).forEach(([sentiment, percentage]) => {
        html += `
            <div class="progress-item">
                <div class="progress-label">
                    <span>${capitalize(sentiment)}</span>
                    <span>${percentage}%</span>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill ${colors[sentiment]}" style="width: ${percentage}%">
                        <span class="progress-value">${percentage}%</span>
                    </div>
                </div>
            </div>
        `;
    });
    
    progressBars.innerHTML = html;
    
    // Animate progress bars
    setTimeout(() => {
        document.querySelectorAll('.progress-fill').forEach(fill => {
            fill.style.width = fill.style.width;
        });
    }, 100);
}

// ===== CLEANUP CHARTS =====
function destroyAllCharts() {
    if (sentimentChart) {
        sentimentChart.destroy();
        sentimentChart = null;
    }
    if (wordChart) {
        wordChart.destroy();
        wordChart = null;
    }
    if (confidenceChart) {
        confidenceChart.destroy();
        confidenceChart = null;
    }
}

// Export functions
window.ChartManager = {
    createSentimentChart,
    createWordChart,
    createConfidenceChart,
    updateProgressBars,
    destroyAllCharts
};