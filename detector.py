"""
质量检测算法模块
结合计算机视觉和机器学习进行产品缺陷检测
"""
import cv2
import numpy as np
from PIL import Image
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import os

class QualityDetector:
    def __init__(self):
        self.scaler = StandardScaler()
        self.is_trained = False
    
    def extract_features(self, image):
        """
        从图像中提取特征
        使用多种计算机视觉特征：
        1. 颜色特征（HSV直方图）
        2. 纹理特征（LBP-like特征）
        3. 边缘特征（Canny边缘检测）
        4. 形状特征（轮廓特征）
        """
        if isinstance(image, Image.Image):
            img_array = np.array(image)
        else:
            img_array = image
        
        # 转换为OpenCV格式（BGR）
        if len(img_array.shape) == 3:
            img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
        else:
            img_bgr = img_array
        
        features = []
        
        # 1. 颜色特征 - HSV直方图
        hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)
        hist_h = cv2.calcHist([hsv], [0], None, [50], [0, 180])
        hist_s = cv2.calcHist([hsv], [1], None, [50], [0, 256])
        hist_v = cv2.calcHist([hsv], [2], None, [50], [0, 256])
        features.extend(hist_h.flatten()[:20])  # 取前20个
        features.extend(hist_s.flatten()[:20])
        features.extend(hist_v.flatten()[:20])
        
        # 2. 纹理特征 - 灰度共生矩阵的简化版本
        gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
        
        # 计算局部二值模式（LBP）的简化版本
        lbp_features = self._calculate_lbp_features(gray)
        features.extend(lbp_features)
        
        # 3. 边缘特征
        edges = cv2.Canny(gray, 50, 150)
        edge_density = np.sum(edges > 0) / (edges.shape[0] * edges.shape[1])
        features.append(edge_density)
        
        # 4. 亮度和对比度
        mean_brightness = np.mean(gray)
        std_brightness = np.std(gray)  # 对比度
        features.extend([mean_brightness, std_brightness])
        
        # 5. 颜色一致性（方差）
        color_variance = np.var(img_bgr.reshape(-1, 3), axis=0)
        features.extend(color_variance.tolist())
        
        return np.array(features)
    
    def _calculate_lbp_features(self, gray_image):
        """计算简化的局部二值模式特征"""
        # 简化的LBP：计算局部区域的亮度变化
        h, w = gray_image.shape
        features = []
        
        # 将图像分成多个区域，计算每个区域的统计特征
        regions = 4
        region_h = h // regions
        region_w = w // regions
        
        for i in range(regions):
            for j in range(regions):
                region = gray_image[i*region_h:(i+1)*region_h, 
                                   j*region_w:(j+1)*region_w]
                features.append(np.mean(region))
                features.append(np.std(region))
        
        return features
    
    def detect_defects(self, image):
        """
        检测产品缺陷
        使用基于规则的方法和特征分析
        """
        if isinstance(image, Image.Image):
            img_array = np.array(image)
        else:
            img_array = image
        
        # 转换为OpenCV格式
        if len(img_array.shape) == 3:
            img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
        else:
            img_bgr = img_array
        
        gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
        
        # 提取特征
        features = self.extract_features(image)
        
        # 缺陷检测逻辑（保持对正常物品的宽容，但提高对异常外观的敏感度）
        defect_scores = {}
        
        # 基础检查：图像质量评估
        mean_brightness = np.mean(gray)
        brightness_std = np.std(gray)
        
        # 如果图像太暗或太亮，降低整体质量分数但不直接判定为不合格
        brightness_penalty = 0.0
        if mean_brightness < 30:  # 太暗
            brightness_penalty = 0.1
        elif mean_brightness > 220:  # 太亮（过曝）
            brightness_penalty = 0.1
        
        # 1. 检测异常颜色区域（可能的污渍或变色）
        # 提高阈值：正常物品颜色变化是正常的，只有极端变化才算异常
        hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)
        color_variance = np.var(hsv[:, :, 0])  # 色调方差
        # 阈值从2000提高到8000，只有非常明显的颜色异常才触发
        if color_variance > 8000:
            defect_scores['color_anomaly'] = min((color_variance - 8000) / 5000, 1.0)
        
        # 1.5. 检测颜色分布不均匀（外观奇怪的特征）
        # 将图像分成多个区域，检测各区域颜色差异
        h, w = hsv.shape[:2]
        regions_h, regions_w = 3, 3
        region_h, region_w = h // regions_h, w // regions_w
        region_colors = []
        for i in range(regions_h):
            for j in range(regions_w):
                region = hsv[i*region_h:(i+1)*region_h, j*region_w:(j+1)*region_w, 0]
                region_colors.append(np.mean(region))
        color_uniformity = np.std(region_colors)  # 区域间颜色差异
        # 如果颜色分布非常不均匀，可能是外观奇怪的物体
        # 提高阈值从25到35，更宽松
        if color_uniformity > 35:  # 阈值提高，更宽松
            defect_scores['color_uniformity'] = min((color_uniformity - 35) / 40, 1.0)
        
        # 2. 检测边缘异常（可能的划痕或裂纹）
        # 使用更严格的Canny参数，减少误检
        edges = cv2.Canny(gray, 80, 200)  # 提高阈值，减少边缘检测
        edge_density = np.sum(edges > 0) / (edges.shape[0] * edges.shape[1])
        # 阈值从0.3提高到0.5，正常物品的边缘密度通常较低
        if edge_density > 0.5:
            defect_scores['edge_anomaly'] = min((edge_density - 0.5) / 0.3, 1.0)
        
        # 3. 检测亮度异常（可能的阴影或反光问题）
        # 阈值从60提高到100，正常物品的亮度变化是允许的
        if brightness_std > 100:
            defect_scores['brightness_anomaly'] = min((brightness_std - 100) / 80, 1.0)
        
        # 4. 检测纹理异常（使用局部方差）
        kernel_size = 15
        kernel = np.ones((kernel_size, kernel_size), np.float32) / (kernel_size * kernel_size)
        local_mean = cv2.filter2D(gray.astype(np.float32), -1, kernel)
        local_variance = cv2.filter2D((gray.astype(np.float32) - local_mean) ** 2, -1, kernel)
        texture_anomaly = np.mean(local_variance)
        # 阈值从500提高到1500，正常纹理变化不算异常
        if texture_anomaly > 1500:
            defect_scores['texture_anomaly'] = min((texture_anomaly - 1500) / 1000, 1.0)
        
        # 5. 检测轮廓异常（可能的形状缺陷）
        # 阈值从10提高到50，正常物品可能有多个轮廓（如按钮、接口等）
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if len(contours) > 50:
            defect_scores['contour_anomaly'] = min((len(contours) - 50) / 30, 1.0)
        
        # 5.5. 检测形状复杂度（外观奇怪的物体通常形状更复杂）
        if len(contours) > 0:
            # 计算最大轮廓的复杂度（周长与面积的比值）
            largest_contour = max(contours, key=cv2.contourArea)
            if cv2.contourArea(largest_contour) > 100:  # 忽略太小的轮廓
                perimeter = cv2.arcLength(largest_contour, True)
                area = cv2.contourArea(largest_contour)
                complexity = perimeter / (area ** 0.5) if area > 0 else 0
                # 正常物品的复杂度通常在10-30之间，稍微降低阈值到45，稍微严格
                if complexity > 45:
                    defect_scores['shape_complexity'] = min((complexity - 45) / 35, 1.0)
        
        # 5.6. 检测轮廓连续性（轮廓不连续可能表示有遮挡）
        if len(contours) > 0:
            # 找到主要轮廓（面积最大的几个）
            sorted_contours = sorted(contours, key=cv2.contourArea, reverse=True)
            main_contours = sorted_contours[:min(3, len(sorted_contours))]  # 取前3个最大轮廓
            
            # 计算轮廓的连续性指标
            # 方法：检查轮廓是否接近闭合，以及是否有明显的断裂
            discontinuity_score = 0.0
            for contour in main_contours:
                if cv2.contourArea(contour) > 500:  # 只检查较大的轮廓
                    # 计算轮廓的凸包
                    hull = cv2.convexHull(contour)
                    hull_area = cv2.contourArea(hull)
                    contour_area = cv2.contourArea(contour)
                    
                    # 如果轮廓面积与凸包面积差异很大，说明轮廓不连续（有凹陷或断裂）
                    if hull_area > 0:
                        solidity = contour_area / hull_area  # 实心度
                        # 实心度越低，说明轮廓越不连续（有遮挡或断裂）
                        if solidity < 0.7:  # 阈值：实心度低于0.7认为不连续
                            discontinuity = 1.0 - solidity
                            discontinuity_score = max(discontinuity_score, discontinuity)
            
            # 检查轮廓数量与面积的关系（多个小轮廓可能表示遮挡）
            if len(contours) > 5:
                # 计算主要轮廓面积占总面积的比例
                total_main_area = sum(cv2.contourArea(c) for c in main_contours[:3])
                total_area = sum(cv2.contourArea(c) for c in contours)
                if total_area > 0:
                    main_area_ratio = total_main_area / total_area
                    # 如果主要轮廓面积占比很小，说明有很多小碎片（可能是遮挡）
                    if main_area_ratio < 0.6:
                        discontinuity_score = max(discontinuity_score, 1.0 - main_area_ratio)
            
            if discontinuity_score > 0.3:  # 阈值：不连续性超过0.3
                defect_scores['contour_discontinuity'] = min((discontinuity_score - 0.3) / 0.4, 1.0)
        
        # 计算综合缺陷分数（改进算法：多指标叠加惩罚）
        if defect_scores:
            max_defect_score = max(defect_scores.values())
            avg_defect_score = np.mean(list(defect_scores.values()))
            
            # 计算异常指标数量（用于多指标叠加惩罚）
            anomaly_count = len(defect_scores)
            
            # 基础分数：稍微提高惩罚系数，从0.5到0.55，稍微严格
            base_score = (max_defect_score * 0.4 + avg_defect_score * 0.6) * 0.55
            
            # 多指标叠加惩罚：如果有多个指标同时异常，提高缺陷分数
            # 这能更好地识别外观奇怪的物体（它们通常有多个异常特征）
            # 稍微提高惩罚强度
            if anomaly_count >= 3:
                # 3个或以上指标异常，显著提高缺陷分数（从10%提高到12%）
                multiplier = 1.0 + (anomaly_count - 2) * 0.12  # 每多一个指标，增加12%
                base_score = min(1.0, base_score * multiplier)
            elif anomaly_count == 2:
                # 2个指标异常，轻微提高（从1.05提高到1.08）
                base_score = min(1.0, base_score * 1.08)
            
            overall_score = base_score
        else:
            overall_score = 0.0
        
        # 添加亮度惩罚
        overall_score = min(1.0, overall_score + brightness_penalty)
        
        # 质量分数（0-100，分数越高质量越好）
        # 改进计算方式：即使有轻微缺陷，也给予一定分数
        if overall_score < 0.3:
            quality_score = 100 - overall_score * 50  # 轻微缺陷，分数在85-100之间
        elif overall_score < 0.6:
            quality_score = 85 - (overall_score - 0.3) * 100  # 中等缺陷，分数在55-85之间
        else:
            quality_score = max(0, 55 - (overall_score - 0.6) * 137.5)  # 严重缺陷，分数在0-55之间
        
        quality_score = max(0, min(100, quality_score))
        
        # 判断是否合格：质量分数低于60分判定为不合格
        is_qualified = quality_score >= 60
        
        # 确定缺陷类型
        defect_type = None
        if not is_qualified and defect_scores:
            max_defect_key = max(defect_scores, key=defect_scores.get)
            if max_defect_key == 'color_anomaly':
                defect_type = '颜色异常'
            elif max_defect_key == 'color_uniformity':
                defect_type = '颜色分布异常'
            elif max_defect_key == 'edge_anomaly':
                defect_type = '边缘缺陷'
            elif max_defect_key == 'brightness_anomaly':
                defect_type = '亮度异常'
            elif max_defect_key == 'texture_anomaly':
                defect_type = '纹理异常'
            elif max_defect_key == 'shape_complexity':
                defect_type = '形状异常'
            elif max_defect_key == 'contour_discontinuity':
                defect_type = '轮廓不连续（可能有遮挡）'
            else:
                defect_type = '轮廓异常'
            
            # 如果多个指标异常，添加综合描述
            if len(defect_scores) >= 3:
                defect_type = '外观异常（多指标异常）'
        
        # 置信度计算：基于缺陷分数的反向映射
        # 改进置信度计算，即使有缺陷也给予合理置信度
        if overall_score < 0.2:
            confidence = 0.95  # 几乎无缺陷，高置信度
        elif overall_score < 0.5:
            confidence = 0.85 - (overall_score - 0.2) * 0.5  # 轻微缺陷，中等置信度
        elif overall_score < 0.7:
            confidence = 0.7 - (overall_score - 0.5) * 1.5  # 中等缺陷，较低置信度
        else:
            confidence = max(0.1, 0.4 - (overall_score - 0.7) * 1.0)  # 严重缺陷，低置信度
        
        confidence = max(0.1, min(0.95, confidence))
        
        result = {
            'qualified': is_qualified,
            'quality_score': round(quality_score, 2),
            'defect_score': round(overall_score, 3),
            'defect_type': defect_type,
            'defect_details': defect_scores,
            'confidence': round(confidence, 3)
        }
        
        return result

