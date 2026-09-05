import sys
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.models.prompt import Prompt
from sentence_transformers import SentenceTransformer

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://wildcard:wildcardpassword@db:5432/wildcard_db")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def backfill():
    db = SessionLocal()
    try:
        prompts = db.query(Prompt).filter(Prompt.embedding == None).all()
        if not prompts:
            print("No prompts require backfilling.")
            return

        print(f"Loading sentence-transformers... this may take a moment.")
        model = SentenceTransformer('all-MiniLM-L6-v2')
        
        for prompt in prompts:
            if prompt.content:
                print(f"Embedding prompt ID: {prompt.id}")
                embedding = model.encode(prompt.content)
                prompt.embedding = embedding.tolist()
                
        db.commit()
        print("Backfill complete.")
    except Exception as e:
        print(f"Error backfilling: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    backfill()
