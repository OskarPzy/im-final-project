"""
Flask主应用
工业产品质量检测系统
"""
from flask import Flask, render_template, request, jsonify, send_file
from camera_utils import CameraCapture
from detector import QualityDetector
from models import Database
import os
from datetime import datetime
import json

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'

# 初始化组件
camera = CameraCapture()
detector = QualityDetector()
db = Database()

# 创建必要的目录
os.makedirs('static/images', exist_ok=True)
os.makedirs('templates', exist_ok=True)
os.makedirs('static/css', exist_ok=True)
os.makedirs('static/js', exist_ok=True)

@app.route('/')
def index():
    """主页"""
    stats = db.get_statistics()
    return render_template('index.html', stats=stats)

@app.route('/history')
def history():
    """检测历史页面"""
    records = db.get_all_records(limit=100)
    return render_template('history.html', records=records)

@app.route('/api/camera/init', methods=['POST'])
def init_camera():
    """初始化摄像头"""
    try:
        if camera.initialize():
            return jsonify({'success': True, 'message': 'Camera initialized successfully'})
        else:
            return jsonify({'success': False, 'message': 'Camera initialization failed, please check camera connection'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

@app.route('/api/camera/capture', methods=['POST'])
def capture_image():
    """捕获图像"""
    try:
        image = camera.capture_image()
        if image is None:
            return jsonify({'success': False, 'message': 'Image capture failed'})
        
        # Convert to base64
        import io
        import base64
        buffered = io.BytesIO()
        image.save(buffered, format="JPEG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        
        return jsonify({
            'success': True,
            'image': img_str
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

@app.route('/api/detect', methods=['POST'])
def detect_quality():
    """执行质量检测"""
    try:
        # Get image data
        data = request.get_json()
        if 'image' not in data:
            return jsonify({'success': False, 'message': 'Missing image data'})
        
        # 解码base64图像
        import base64
        import io
        from PIL import Image
        
        image_data = data['image'].split(',')[1] if ',' in data['image'] else data['image']
        image_bytes = base64.b64decode(image_data)
        image = Image.open(io.BytesIO(image_bytes))
        
        # 执行检测
        result = detector.detect_defects(image)
        
        # 保存图像（可选）
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        image_filename = f'static/images/detection_{timestamp}.jpg'
        image.save(image_filename)
        
        # Save detection record
        record_id = db.add_record(
            result='Passed' if result['qualified'] else 'Failed',
            confidence=result['confidence'],
            image_path=image_filename,
            defect_type=result['defect_type'],
            quality_score=result['quality_score']
        )
        
        # 将result转换为可JSON序列化的格式
        # 确保所有值都是Python原生类型，而不是NumPy类型
        serializable_result = {
            'qualified': bool(result['qualified']),  # 确保是Python bool类型
            'quality_score': float(result['quality_score']),
            'defect_score': float(result['defect_score']),
            'defect_type': result['defect_type'] if result['defect_type'] is not None else None,
            'defect_details': {k: float(v) for k, v in result['defect_details'].items()},  # 转换NumPy类型为float
            'confidence': float(result['confidence'])
        }
        
        return jsonify({
            'success': True,
            'result': serializable_result,
            'record_id': record_id
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'Detection error: {str(e)}'})

@app.route('/api/camera/release', methods=['POST'])
def release_camera():
    """释放摄像头"""
    try:
        camera.release()
        return jsonify({'success': True, 'message': 'Camera released'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

@app.route('/api/statistics', methods=['GET'])
def get_statistics():
    """获取统计信息"""
    try:
        stats = db.get_statistics()
        return jsonify({'success': True, 'data': stats})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

@app.route('/api/records', methods=['GET'])
def get_records():
    """获取检测记录"""
    try:
        limit = request.args.get('limit', 100, type=int)
        records = db.get_all_records(limit=limit)
        
        # Convert to dictionary list
        records_list = []
        for record in records:
            records_list.append({
                'id': record[0],
                'timestamp': record[1],
                'result': record[2],
                'confidence': record[3],
                'defect_type': record[4],
                'quality_score': record[5]
            })
        
        return jsonify({'success': True, 'data': records_list})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

if __name__ == '__main__':
    print("=" * 50)
    print("Industrial Product Quality Detection System")
    print("=" * 50)
    print("Starting server...")
    print("Please access in browser: http://localhost:5000")
    print("=" * 50)
    app.run(debug=True, host='0.0.0.0', port=5000)

