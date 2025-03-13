from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
import logging
import numpy as np
import math
import uvicorn

# Set up logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="Music-Picture Color Matching API",
              description="API for matching music to pictures based on color analysis",
              version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Define data models
class ColorVector(BaseModel):
    values: List[float]


class MusicKeywords(BaseModel):
    keywords: List[str]


class MusicItem(BaseModel):
    id: str
    name: str
    artist: Optional[str] = None
    keywords: List[str]


class MatchRequest(BaseModel):
    color_vector: ColorVector
    music_items: List[MusicItem]


class MatchResult(BaseModel):
    music_id: str
    match_score: float


class MatchResponse(BaseModel):
    matched_items: List[MatchResult]


# Color-keyword mapping (same as in the Android app)
KEYWORD_COLOR_MAP = {
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


def calculate_color_similarity(color1: List[float], color2: List[float]) -> float:
    """
    Calculate color similarity using cosine similarity
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


def calculate_match_score(keywords: List[str], color_vector: List[float]) -> float:
    """
    Calculate match score between keywords and color vector
    """
    total_score = 0
    matched_keywords = 0

    for keyword in keywords:
        if keyword in KEYWORD_COLOR_MAP:
            keyword_color = KEYWORD_COLOR_MAP[keyword]
            similarity = calculate_color_similarity(keyword_color, color_vector)
            total_score += similarity
            matched_keywords += 1

    # If no keywords matched, return a random value
    if matched_keywords == 0:
        return np.random.random()

    # Return average match score
    return total_score / matched_keywords


@app.post("/match", response_model=MatchResponse)
async def match_music(request: MatchRequest):
    """
    Match music items to a color vector
    """
    logger.info(f"Received match request for {len(request.music_items)} music items")

    try:
        # Extract color vector
        color_vector = request.color_vector.values

        # Calculate match scores for each music item
        results = []
        for music_item in request.music_items:
            match_score = calculate_match_score(music_item.keywords, color_vector)
            results.append(MatchResult(
                music_id=music_item.id,
                match_score=match_score
            ))

        # Sort results by match score (descending)
        results.sort(key=lambda x: x.match_score, reverse=True)

        logger.info(f"Successfully matched {len(results)} items")
        return MatchResponse(matched_items=results)

    except Exception as e:
        logger.error(f"Error processing match request: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")


@app.get("/")
async def root():
    """
    Root endpoint for health check
    """
    return {"status": "healthy", "message": "Music-Picture Color Matching API is running"}


if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)