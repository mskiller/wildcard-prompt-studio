import sys
import os
import shutil
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.models.image import Image
from app.models.prompt import Prompt

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://wildcard:wildcardpassword@db:5432/wildcard_db")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def seed_image():
    db = SessionLocal()
    try:
        # Get or create a prompt
        prompt = db.query(Prompt).first()
        if not prompt:
            prompt = Prompt(name="Test Prompt", content="A beautiful sunset", author="System")
            db.add(prompt)
            db.commit()
            db.refresh(prompt)
        
        # Check if dummy image exists
        existing = db.query(Image).filter(Image.filename == "dummy_sunset.png").first()
        if not existing:
            image = Image(
                filename="dummy_sunset.png",
                prompt_id=prompt.id,
                seed=123456789,
                cfg_scale=7.5,
                steps=20,
                sampler_name="euler_a",
                width=512,
                height=512
            )
            db.add(image)
            db.commit()
            print("Database seeded with dummy image.")
            
            # Create a dummy image file in static
            os.makedirs("app/static/images", exist_ok=True)
            with open("app/static/images/dummy_sunset.png", "wb") as f:
                # 1x1 black pixel PNG
                f.write(b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\rIDATx\x9cc\xf8\xff\xff?\x00\x05\xfe\x02\xfe\x00\x00\x00\x00\x00\x00IEND\xaeB`\x82')
            print("Dummy image file created.")
    except Exception as e:
        print(f"Error seeding DB: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_image()
