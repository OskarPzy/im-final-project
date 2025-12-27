// 主页面JavaScript
let stream = null;
let videoElement = document.getElementById('videoElement');
let canvasElement = document.getElementById('canvasElement');
let startBtn = document.getElementById('startBtn');
let captureBtn = document.getElementById('captureBtn');
let stopBtn = document.getElementById('stopBtn');
let resultContainer = document.getElementById('resultContainer');
let noVideo = document.getElementById('noVideo');

// 初始化摄像头
startBtn.addEventListener('click', async () => {
    try {
        // 调用后端API初始化摄像头
        const response = await fetch('/api/camera/init', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const data = await response.json();
        
        if (data.success) {
            // 获取用户媒体流
            stream = await navigator.mediaDevices.getUserMedia({
                video: {
                    width: { ideal: 640 },
                    height: { ideal: 480 }
                }
            });
            
            videoElement.srcObject = stream;
            videoElement.style.display = 'block';
            noVideo.style.display = 'none';
            
            startBtn.disabled = true;
            captureBtn.disabled = false;
            stopBtn.disabled = false;
            
            showMessage('Camera started', 'success');
        } else {
            showMessage(data.message || 'Camera initialization failed', 'error');
        }
    } catch (error) {
        console.error('Camera startup error:', error);
        showMessage('Unable to access camera, please check permissions', 'error');
    }
});

// Capture and detect
captureBtn.addEventListener('click', async () => {
    if (!stream) {
        showMessage('Please start the camera first', 'error');
        return;
    }
    
    try {
        // Draw current video frame on canvas
        const ctx = canvasElement.getContext('2d');
        canvasElement.width = videoElement.videoWidth;
        canvasElement.height = videoElement.videoHeight;
        ctx.drawImage(videoElement, 0, 0);
        
        // Convert to base64
        const imageData = canvasElement.toDataURL('image/jpeg', 0.8);
        
        // Show loading state
        resultContainer.innerHTML = '<div class="placeholder-message"><p>Detecting...</p></div>';
        captureBtn.disabled = true;
        
        // Send to backend for detection
        const response = await fetch('/api/detect', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                image: imageData
            })
        });
        
        const data = await response.json();
        captureBtn.disabled = false;
        
        if (data.success) {
            displayResult(data.result);
            // Refresh statistics
            updateStatistics();
        } else {
            showMessage(data.message || 'Detection failed', 'error');
            resultContainer.innerHTML = '<div class="placeholder-message"><p>Detection failed, please retry</p></div>';
        }
    } catch (error) {
        console.error('Detection error:', error);
        showMessage('Error occurred during detection', 'error');
        captureBtn.disabled = false;
    }
});

// 停止检测
stopBtn.addEventListener('click', () => {
    if (stream) {
        stream.getTracks().forEach(track => track.stop());
        stream = null;
    }
    
    videoElement.srcObject = null;
    videoElement.style.display = 'none';
    noVideo.style.display = 'block';
    
    // 调用后端释放摄像头
    fetch('/api/camera/release', {
        method: 'POST'
    });
    
    startBtn.disabled = false;
    captureBtn.disabled = true;
    stopBtn.disabled = true;
    
    showMessage('Camera closed', 'info');
});

// Display detection result
function displayResult(result) {
    const qualified = result.qualified;
    const qualityScore = result.quality_score;
    const defectType = result.defect_type || 'None';
    const confidence = (result.confidence * 100).toFixed(1);
    
    let html = `
        <div class="result-item ${qualified ? 'success' : 'danger'}">
            <div class="result-label">Detection Result</div>
            <div class="result-value">
                <span class="badge ${qualified ? 'badge-success' : 'badge-danger'}">
                    ${qualified ? '✅ Passed' : '❌ Failed'}
                </span>
            </div>
        </div>
        
        <div class="result-item">
            <div class="result-label">Quality Score</div>
            <div class="result-value">${qualityScore} / 100</div>
        </div>
        
        <div class="result-item">
            <div class="result-label">Confidence</div>
            <div class="result-value">${confidence}%</div>
        </div>
    `;
    
    if (!qualified) {
        html += `
            <div class="result-item danger">
                <div class="result-label">Defect Type</div>
                <div class="result-value">${defectType}</div>
            </div>
        `;
    }
    
    resultContainer.innerHTML = html;
}

// 更新统计信息（使用AJAX，不刷新页面）
async function updateStatistics() {
    try {
        const response = await fetch('/api/statistics');
        const data = await response.json();
        
        if (data.success) {
            const stats = data.data;
            // 更新统计信息DOM，不刷新页面
            const statTotal = document.getElementById('statTotal');
            const statPassed = document.getElementById('statPassed');
            const statFailed = document.getElementById('statFailed');
            const statPassRate = document.getElementById('statPassRate');
            
            if (statTotal) statTotal.textContent = stats.total;
            if (statPassed) statPassed.textContent = stats.passed;
            if (statFailed) statFailed.textContent = stats.failed;
            if (statPassRate) statPassRate.textContent = stats.pass_rate.toFixed(1) + '%';
        }
    } catch (error) {
        console.error('Failed to update statistics:', error);
        // Silent failure, don't affect detection result display
    }
}

// 显示消息
function showMessage(message, type = 'info') {
    // 简单的消息提示（可以改进为更美观的提示框）
    const colors = {
        success: '#84fab0',
        error: '#fa709a',
        info: '#667eea'
    };
    
    const messageDiv = document.createElement('div');
    messageDiv.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 15px 25px;
        background: ${colors[type] || colors.info};
        color: white;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        z-index: 1000;
        font-weight: bold;
    `;
    messageDiv.textContent = message;
    
    document.body.appendChild(messageDiv);
    
    setTimeout(() => {
        messageDiv.remove();
    }, 3000);
}

// 页面卸载时释放摄像头
window.addEventListener('beforeunload', () => {
    if (stream) {
        stream.getTracks().forEach(track => track.stop());
    }
    fetch('/api/camera/release', {
        method: 'POST'
    });
});

