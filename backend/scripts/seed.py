import sys
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.models.model_profile import ModelProfile

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://wildcard:wildcardpassword@db:5432/wildcard_db")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

DEFAULT_PROFILES = [
    {
        "name": "SDXL",
        "description": "Base SDXL 1.0 architecture",
        "default_negative_prompt": "text, watermark, ugly, low quality, worst quality, bad anatomy, bad hands, missing fingers",
        "trigger_words": "",
        "custom_rules": "Use natural language phrasing instead of comma-separated booru tags. Emphasize lighting and camera angles."
    },
    {
        "name": "Illustrious",
        "description": "Illustrious XL architecture",
        "default_negative_prompt": "lowres, bad anatomy, bad hands, text, error, missing fingers, extra digit, fewer digits, cropped, worst quality, low quality, normal quality, jpeg artifacts, signature, watermark, username, blurry",
        "trigger_words": "masterpiece, best quality, ultra-detailed, illustration",
        "custom_rules": "Strictly use Danbooru tags separated by commas. Start with copyright, character, then visual tags."
    },
    {
        "name": "NoobAI",
        "description": "NoobAI SDXL model",
        "default_negative_prompt": "lowres, bad anatomy, bad hands, text, error, missing fingers, extra digit, fewer digits, cropped, worst quality, low quality, normal quality, jpeg artifacts, signature, watermark, username, blurry",
        "trigger_words": "masterpiece, best quality, very aesthetic, absurdres",
        "custom_rules": "Requires quality tags. Use Danbooru syntax."
    },
    {
        "name": "Ideogram",
        "description": "Ideogram API",
        "default_negative_prompt": "ugly, deformed, watermark",
        "trigger_words": "",
        "custom_rules": "Ideogram responds extremely well to typographic prompts. Clearly quote text you want rendered."
    },
    {
        "name": "Krea 2",
        "description": "Krea 2 natural language image generation model",
        "default_negative_prompt": "",
        "trigger_words": "",
        "custom_rules": "Faithfulness first. Direct T2I natural language structure: [Subject] in [Setting] with [Lighting/Camera Optics]. Automatically wrap text targets in double quotes like \"hello world\". Do not use SD anti-patterns like 8k, masterpiece, or hyper-detailed."
    },
    {
        "name": "ANIMA",
        "description": "ANIMA Anime/Illustrative AI generation model profile",
        "default_negative_prompt": "lowres, bad anatomy, bad hands, text, error, missing fingers, extra digit, fewer digits, cropped, worst quality, low quality, normal quality, jpeg artifacts, signature, watermark, username, blurry",
        "trigger_words": "score_9, score_8, score_7, anime",
        "custom_rules": "Prepend ANIMA quality score tags (score_9, score_8, score_7). Use @artist_name syntax for artists. Do not use SD-style weight syntax like (tag:1.2)."
    }
]


def seed():
    db = SessionLocal()
    try:
        for profile_data in DEFAULT_PROFILES:
            existing = db.query(ModelProfile).filter(ModelProfile.name == profile_data["name"]).first()
            if not existing:
                profile = ModelProfile(**profile_data)
                db.add(profile)
                print(f"Added profile: {profile_data['name']}")
        db.commit()
        print("Database seeded with default model profiles.")
    except Exception as e:
        print(f"Error seeding DB: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed()
