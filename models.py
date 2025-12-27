"""
数据库模型定义
"""
from datetime import datetime
import sqlite3
import os

class Database:
    def __init__(self, db_path='quality_detection.db'):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """初始化数据库表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS detection_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                result TEXT NOT NULL,
                confidence REAL,
                image_path TEXT,
                defect_type TEXT,
                quality_score REAL
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def add_record(self, result, confidence, image_path=None, defect_type=None, quality_score=None):
        """添加检测记录"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        cursor.execute('''
            INSERT INTO detection_records 
            (timestamp, result, confidence, image_path, defect_type, quality_score)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (timestamp, result, confidence, image_path, defect_type, quality_score))
        
        conn.commit()
        record_id = cursor.lastrowid
        conn.close()
        
        return record_id
    
    def get_all_records(self, limit=100):
        """获取所有检测记录"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, timestamp, result, confidence, defect_type, quality_score
            FROM detection_records
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (limit,))
        
        records = cursor.fetchall()
        conn.close()
        
        return records
    
    def get_statistics(self):
        """获取统计信息"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 总检测次数
        cursor.execute('SELECT COUNT(*) FROM detection_records')
        total = cursor.fetchone()[0]
        
        # 合格数量
        cursor.execute('SELECT COUNT(*) FROM detection_records WHERE result = ?', ('合格',))
        passed = cursor.fetchone()[0]
        
        # 不合格数量
        cursor.execute('SELECT COUNT(*) FROM detection_records WHERE result = ?', ('不合格',))
        failed = cursor.fetchone()[0]
        
        # 平均质量分数
        cursor.execute('SELECT AVG(quality_score) FROM detection_records WHERE quality_score IS NOT NULL')
        avg_score = cursor.fetchone()[0] or 0
        
        conn.close()
        
        return {
            'total': total,
            'passed': passed,
            'failed': failed,
            'pass_rate': (passed / total * 100) if total > 0 else 0,
            'avg_score': round(avg_score, 2)
        }

