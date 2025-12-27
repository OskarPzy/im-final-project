// 历史页面JavaScript
let chart = null;

// 页面加载时初始化图表
document.addEventListener('DOMContentLoaded', () => {
    initChart();
    
    // 刷新按钮
    document.getElementById('refreshBtn').addEventListener('click', () => {
        location.reload();
    });
});

// 初始化统计图表
async function initChart() {
    try {
        const response = await fetch('/api/statistics');
        const data = await response.json();
        
        if (data.success) {
            const stats = data.data;
            
            const ctx = document.getElementById('statisticsChart').getContext('2d');
            
            // 销毁旧图表
            if (chart) {
                chart.destroy();
            }
            
            // Create new chart
            chart = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: ['Total Detections', 'Passed', 'Failed'],
                    datasets: [{
                        label: 'Detection Statistics',
                        data: [stats.total, stats.passed, stats.failed],
                        backgroundColor: [
                            'rgba(102, 126, 234, 0.8)',
                            'rgba(132, 250, 176, 0.8)',
                            'rgba(250, 112, 154, 0.8)'
                        ],
                        borderColor: [
                            'rgba(102, 126, 234, 1)',
                            'rgba(132, 250, 176, 1)',
                            'rgba(250, 112, 154, 1)'
                        ],
                        borderWidth: 2
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: true,
                    plugins: {
                        legend: {
                            display: false
                        },
                        title: {
                            display: true,
                            text: 'Detection Data Statistics',
                            font: {
                                size: 18
                            }
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: {
                                stepSize: 1
                            }
                        }
                    }
                }
            });
            
            // 创建饼图显示合格率
            createPieChart(stats);
        }
    } catch (error) {
        console.error('Failed to load statistics:', error);
    }
}

// 创建合格率饼图
function createPieChart(stats) {
    // 在图表容器中添加饼图
    const chartContainer = document.querySelector('.chart-container');
    
    // 创建饼图canvas
    const pieCanvas = document.createElement('canvas');
    pieCanvas.id = 'pieChart';
    pieCanvas.style.marginTop = '30px';
    chartContainer.appendChild(pieCanvas);
    
    const ctx = pieCanvas.getContext('2d');
    
    const pieChart = new Chart(ctx, {
        type: 'pie',
        data: {
            labels: ['Passed', 'Failed'],
            datasets: [{
                data: [stats.passed, stats.failed],
                backgroundColor: [
                    'rgba(132, 250, 176, 0.8)',
                    'rgba(250, 112, 154, 0.8)'
                ],
                borderColor: [
                    'rgba(132, 250, 176, 1)',
                    'rgba(250, 112, 154, 1)'
                ],
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                title: {
                    display: true,
                    text: `Pass Rate: ${stats.pass_rate.toFixed(1)}%`,
                    font: {
                        size: 18
                    }
                },
                legend: {
                    position: 'bottom'
                }
            }
        }
    });
}

