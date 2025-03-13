import numpy as np
from typing import List, Dict, Tuple, Optional


class ColorMatchService:
    """
    Service for matching colors to music keywords
    """

    def __init__(self):
        # Initialize keyword-color mapping
        self.keyword_color_map = self._initialize_keyword_color_map()

    def _initialize_keyword_color_map(self) -> Dict[str, List[float]]:
        """
        Initialize the mapping between keywords and colors
        """
        return {
            "快乐": [1.0, 1.0, 0.0],  # 黄色
            "悲伤": [0.0, 0.0, 0.8],  # 蓝色
            "激动": [1.0, 0.0, 0.0],  # 红色
            "平静": [0.5, 0.7, 1.0],  # 淡蓝色
            "忧郁": [0.5, 0.5, 0.7],  # 灰蓝色
            "兴奋": [1.0, 0.5, 0.0],  # 橙色
            "温暖": [1.0, 0.8, 0.6],  # 暖色
            "冷淡": [0.6, 0.8, 0.8],  # 冷色
            "明亮": [1.0, 1.0, 0.8],  # 亮色
            "黑暗": [0.2, 0.2, 0.2],  # 暗色
            "活力": [0.8, 0.2, 0.8],  # 紫色
            "疲惫": [0.5, 0.5, 0.5],  # 灰色
            "热情": [1.0, 0.2, 0.2],  # 红色
            "冷静": [0.0, 0.5, 0.5],  # 青色
            "柔和": [0.8, 0.8, 1.0],  # 淡紫色
            "强烈": [0.9, 0.1, 0.1],  # 深红色
            "轻快": [0.7, 1.0, 0.7],  # 淡绿色
            "沉重": [0.3, 0.3, 0.4],  # 深灰色
            "清新": [0.4, 0.8, 0.4],  # 绿色
            "浑浊": [0.5, 0.4, 0.3],  # 棕色
            "甜蜜": [1.0, 0.7, 0.7],  # 粉色
            "苦涩": [0.3, 0.2, 0.1],  # 深棕色
            "欢快": [0.9, 0.9, 0.0],  # 黄色
            "忧伤": [0.1, 0.3, 0.6],  # 灰蓝色
            "阳光": [1.0, 0.9, 0.5],  # 暖黄色
            "阴雨": [0.5, 0.5, 0.6],  # 灰色
            "彩虹": [0.6, 0.0, 0.6],  # 紫色
            "灰暗": [0.4, 0.4, 0.4],  # 灰色
            "春天": [0.7, 0.9, 0.5],  # 嫩绿色
            "夏天": [0.0, 0.8, 1.0],  # 蓝绿色
            "秋天": [0.8, 0.5, 0.2],  # 橙褐色
            "冬天": [0.9, 0.9, 0.9],  # 白色
        }

    def calculate_color_similarity(self, color1: List[float], color2: List[float]) -> float:
        """
        Calculate the similarity between two color vectors using cosine similarity
        """
        # Make sure we're using the first 3 values (RGB)
        c1 = np.array(color1[:3])
        c2 = np.array(color2[:3])

        # Calculate dot product
        dot_product = np.dot(c1, c2)

        # Calculate norms
        norm1 = np.linalg.norm(c1)
        norm2 = np.linalg.norm(c2)

        # Avoid division by zero
        if norm1 == 0 or norm2 == 0:
            return 0

        # Calculate cosine similarity
        similarity = dot_product / (norm1 * norm2)

        return float(similarity)

    def match_keywords_to_color(self, keywords: List[str], color_vector: List[float]) -> Tuple[float, List[str]]:
        """
        Match keywords to a color vector and return a match score
        Also returns the list of matched keywords
        """
        total_score = 0
        matched_keywords = []

        for keyword in keywords:
            if keyword in self.keyword_color_map:
                keyword_color = self.keyword_color_map[keyword]
                similarity = self.calculate_color_similarity(keyword_color, color_vector)
                total_score += similarity
                matched_keywords.append(keyword)

        # If no keywords matched, return a random value
        if not matched_keywords:
            return np.random.random(), []

        # Return average match score and matched keywords
        return total_score / len(matched_keywords), matched_keywords

    def analyze_colors(self, colors: Dict[str, List[float]]) -> Dict[str, float]:
        """
        Analyze a set of colors and determine their emotional associations
        Returns a dictionary mapping emotion keywords to strength values
        """
        emotions = {}

        # For each color (e.g., dominant, vibrant, etc.)
        for color_name, color_vector in colors.items():
            # For each keyword in our mapping
            for keyword, keyword_color in self.keyword_color_map.items():
                # Calculate similarity
                similarity = self.calculate_color_similarity(keyword_color, color_vector)

                # Add to emotions dictionary with a weight based on the color type
                weight = 1.0
                if color_name == "dominant":
                    weight = 2.0
                elif color_name == "vibrant":
                    weight = 1.5

                # Update emotion value
                if keyword in emotions:
                    emotions[keyword] = max(emotions[keyword], similarity * weight)
                else:
                    emotions[keyword] = similarity * weight

        # Normalize values
        max_value = max(emotions.values()) if emotions else 1.0
        for keyword in emotions:
            emotions[keyword] /= max_value

        return emotions

    def generate_color_variations(self, base_color: List[float], count: int = 5) -> List[List[float]]:
        """
        Generate variations of a color for creating a visually coherent slideshow
        """
        variations = [base_color]

        # Convert to numpy array for easier manipulation
        base = np.array(base_color[:3])

        # Generate variations
        for i in range(count - 1):
            # Adjust hue, saturation, or brightness
            variation_type = i % 3
            factor = 0.2 + (i * 0.1)  # Increasing variation

            if variation_type == 0:
                # Adjust brightness
                variation = base * (1.0 + factor)
            elif variation_type == 1:
                # Adjust saturation
                brightness = np.mean(base)
                variation = base + (base - brightness) * factor
            else:
                # Shift hue (rotate in color space)
                # This is a simplified approach - a proper hue shift would use HSL conversion
                variation = np.roll(base, 1)

            # Clip values to [0, 1]
            variation = np.clip(variation, 0, 1)

            # Add to variations list
            variations.append(variation.tolist())

        return variations