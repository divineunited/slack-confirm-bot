"""
Test script to verify database connectivity and persistence
"""
import os
import sys
from datetime import datetime

from dotenv import load_dotenv
from sqlalchemy import inspect

from .models import Announcement, Base, ReadReceipt, SessionLocal, Target, engine

# Load environment variables
load_dotenv()

def test_database_connection():
    """Test connection to the database"""
    try:
        # Try to connect to the database
        connection = engine.connect()
        connection.close()
        print("✅ Successfully connected to the database")
        return True
    except Exception as e:
        print(f"❌ Failed to connect to the database: {e}")
        return False

def check_tables_exist():
    """Check if all required tables exist in the database"""
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    required_tables = ["announcements", "targets", "read_receipts"]
    missing_tables = [table for table in required_tables if table not in tables]
    
    if missing_tables:
        print(f"❌ Missing tables: {', '.join(missing_tables)}")
        return False
    else:
        print(f"✅ All required tables exist: {', '.join(required_tables)}")
        return True

def create_and_verify_test_data():
    """Create test data and verify it was persisted"""
    db = SessionLocal()
    
    # Create a test announcement with a unique identifier
    test_id = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    test_text = f"Test announcement {test_id}"
    
    print(f"Creating test announcement with text: '{test_text}'")
    
    # Create announcement
    ann = Announcement(
        owner_id="U_TEST",
        channel_id="C_TEST",
        message_ts=f"{test_id}.123456",
        text=test_text
    )
    db.add(ann)
    db.commit()
    db.refresh(ann)
    announcement_id = ann.id
    print(f"✅ Created announcement with ID: {announcement_id}")
    
    # Create target
    tgt = Target(
        announcement_id=announcement_id,
        user_id="U_TARGET_TEST"
    )
    db.add(tgt)
    db.commit()
    db.refresh(tgt)
    target_id = tgt.id
    print(f"✅ Created target with ID: {target_id}")
    
    # Create read receipt
    receipt = ReadReceipt(
        target_id=target_id,
        timestamp=datetime.utcnow()
    )
    db.add(receipt)
    db.commit()
    db.refresh(receipt)
    receipt_id = receipt.id
    print(f"✅ Created read receipt with ID: {receipt_id}")
    
    # Close the session
    db.close()
    
    # Open a new session to verify data was persisted
    print("\nVerifying data persistence...")
    db = SessionLocal()
    
    # Verify announcement
    saved_ann = db.query(Announcement).filter_by(id=announcement_id).first()
    if saved_ann and saved_ann.text == test_text:
        print(f"✅ Successfully retrieved announcement with ID {announcement_id}")
    else:
        print(f"❌ Failed to retrieve announcement with ID {announcement_id}")
    
    # Verify target
    saved_tgt = db.query(Target).filter_by(id=target_id).first()
    if saved_tgt and saved_tgt.announcement_id == announcement_id:
        print(f"✅ Successfully retrieved target with ID {target_id}")
    else:
        print(f"❌ Failed to retrieve target with ID {target_id}")
    
    # Verify read receipt
    saved_receipt = db.query(ReadReceipt).filter_by(id=receipt_id).first()
    if saved_receipt and saved_receipt.target_id == target_id:
        print(f"✅ Successfully retrieved read receipt with ID {receipt_id}")
    else:
        print(f"❌ Failed to retrieve read receipt with ID {receipt_id}")
    
    # Close the session
    db.close()
    
    # Return True if all verifications passed
    return saved_ann and saved_tgt and saved_receipt

def run_all_tests():
    """Run all database tests"""
    print("=== Testing Database Connection and Persistence ===\n")
    
    # Test database connection
    if not test_database_connection():
        print("\n❌ Database connection test failed. Exiting.")
        return False
    
    print()  # Empty line for readability
    
    # Check if tables exist
    if not check_tables_exist():
        print("\n❌ Table check failed. Try running the migration script first.")
        return False
    
    print()  # Empty line for readability
    
    # Create and verify test data
    if not create_and_verify_test_data():
        print("\n❌ Data persistence test failed.")
        return False
    
    print("\n✅ All database tests passed successfully!")
    return True

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
