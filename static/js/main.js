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
            
            showMessage('摄像头已启动', 'success');
        } else {
            showMessage(data.message || '摄像头初始化失败', 'error');
        }
    } catch (error) {
        console.error('摄像头启动错误:', error);
        showMessage('无法访问摄像头，请检查权限设置', 'error');
    }
});

// 拍摄并检测
captureBtn.addEventListener('click', async () => {
    if (!stream) {
        showMessage('请先启动摄像头', 'error');
        return;
    }
    
    try {
        // 在canvas上绘制当前视频帧
        const ctx = canvasElement.getContext('2d');
        canvasElement.width = videoElement.videoWidth;
        canvasElement.height = videoElement.videoHeight;
        ctx.drawImage(videoElement, 0, 0);
        
        // 转换为base64
        const imageData = canvasElement.toDataURL('image/jpeg', 0.8);
        
        // 显示加载状态
        resultContainer.innerHTML = '<div class="placeholder-message"><p>正在检测中...</p></div>';
        captureBtn.disabled = true;
        
        // 发送到后端进行检测
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
            // 刷新统计信息
            updateStatistics();
        } else {
            showMessage(data.message || '检测失败', 'error');
            resultContainer.innerHTML = '<div class="placeholder-message"><p>检测失败，请重试</p></div>';
        }
    } catch (error) {
        console.error('检测错误:', error);
        showMessage('检测过程中发生错误', 'error');
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
    
    showMessage('摄像头已关闭', 'info');
});

// 显示检测结果
function displayResult(result) {
    const qualified = result.qualified;
    const qualityScore = result.quality_score;
    const defectType = result.defect_type || '无';
    const confidence = (result.confidence * 100).toFixed(1);
    
    let html = `
        <div class="result-item ${qualified ? 'success' : 'danger'}">
            <div class="result-label">检测结果</div>
            <div class="result-value">
                <span class="badge ${qualified ? 'badge-success' : 'badge-danger'}">
                    ${qualified ? '✅ 合格' : '❌ 不合格'}
                </span>
            </div>
        </div>
        
        <div class="result-item">
            <div class="result-label">质量分数</div>
            <div class="result-value">${qualityScore} / 100</div>
        </div>
        
        <div class="result-item">
            <div class="result-label">置信度</div>
            <div class="result-value">${confidence}%</div>
        </div>
    `;
    
    if (!qualified) {
        html += `
            <div class="result-item danger">
                <div class="result-label">缺陷类型</div>
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
        console.error('更新统计信息失败:', error);
        // 静默失败，不影响检测结果显示
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

