import os
from datetime import datetime

from dotenv import load_dotenv
from .models import Announcement, Base, ReadReceipt, SessionLocal, Target, engine

# Load environment variables
load_dotenv()

# Create database tables
Base.metadata.create_all(bind=engine)

def create_test_data():
    """Create test data for manual testing"""
    db = SessionLocal()
    
    # Create a test announcement
    ann = Announcement(
        owner_id="U12345",
        channel_id="C12345",
        message_ts="1234567890.123456",
        text="This is a test announcement"
    )
    db.add(ann)
    db.commit()
    db.refresh(ann)
    print(f"Created announcement: {ann.id}")
    
    # Create test targets
    targets = []
    for user_id in ["U67890", "U13579"]:
        tgt = Target(
            announcement_id=ann.id,
            user_id=user_id
        )
        db.add(tgt)
        db.commit()
        db.refresh(tgt)
        targets.append(tgt)
        print(f"Created target: {tgt.id} for user {user_id}")
    
    # Create a read receipt for one target
    receipt = ReadReceipt(
        target_id=targets[0].id,
        timestamp=datetime.utcnow()
    )
    db.add(receipt)
    db.commit()
    db.refresh(receipt)
    print(f"Created read receipt: {receipt.id} for target {targets[0].id}")
    
    db.close()
    print("Test data created successfully!")

if __name__ == "__main__":
    create_test_data()
