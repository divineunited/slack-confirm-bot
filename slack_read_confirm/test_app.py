import os
import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch

from dotenv import load_dotenv
from .models import Announcement, Base, ReadReceipt, SessionLocal, Target, engine
from .scheduler import schedule_user_reminder

# Load environment variables
load_dotenv()

# Create test database
Base.metadata.create_all(bind=engine)

class TestSlackReadConfirm(unittest.TestCase):
    def setUp(self):
        self.db = SessionLocal()
        # Clear database before each test
        self.db.query(ReadReceipt).delete()
        self.db.query(Target).delete()
        self.db.query(Announcement).delete()
        self.db.commit()
        
    def tearDown(self):
        self.db.close()
        
    def test_create_announcement(self):
        # Create test announcement
        ann = Announcement(
            owner_id="U12345",
            channel_id="C12345",
            message_ts="1234567890.123456",
            text="Test announcement"
        )
        self.db.add(ann)
        self.db.commit()
        self.db.refresh(ann)
        
        # Verify announcement was created
        saved_ann = self.db.query(Announcement).filter_by(id=ann.id).first()
        self.assertIsNotNone(saved_ann)
        self.assertEqual(saved_ann.text, "Test announcement")
        
    def test_create_target(self):
        # Create test announcement
        ann = Announcement(
            owner_id="U12345",
            channel_id="C12345",
            message_ts="1234567890.123456",
            text="Test announcement"
        )
        self.db.add(ann)
        self.db.commit()
        self.db.refresh(ann)
        
        # Create target
        tgt = Target(
            announcement_id=ann.id,
            user_id="U67890"
        )
        self.db.add(tgt)
        self.db.commit()
        self.db.refresh(tgt)
        
        # Verify target was created
        saved_tgt = self.db.query(Target).filter_by(id=tgt.id).first()
        self.assertIsNotNone(saved_tgt)
        self.assertEqual(saved_tgt.user_id, "U67890")
        
    def test_create_read_receipt(self):
        # Create test announcement
        ann = Announcement(
            owner_id="U12345",
            channel_id="C12345",
            message_ts="1234567890.123456",
            text="Test announcement"
        )
        self.db.add(ann)
        self.db.commit()
        self.db.refresh(ann)
        
        # Create target
        tgt = Target(
            announcement_id=ann.id,
            user_id="U67890"
        )
        self.db.add(tgt)
        self.db.commit()
        self.db.refresh(tgt)
        
        # Create read receipt
        receipt = ReadReceipt(
            target_id=tgt.id,
            timestamp=datetime.utcnow()
        )
        self.db.add(receipt)
        self.db.commit()
        self.db.refresh(receipt)
        
        # Verify read receipt was created
        saved_receipt = self.db.query(ReadReceipt).filter_by(id=receipt.id).first()
        self.assertIsNotNone(saved_receipt)
        self.assertEqual(saved_receipt.target_id, tgt.id)
        
    @patch('slack_read_confirm.scheduler.app')
    def test_scheduler(self, mock_app):
        # Mock the Slack client
        mock_client = MagicMock()
        mock_app.client = mock_client
        
        # Create test announcement
        ann = Announcement(
            owner_id="U12345",
            channel_id="C12345",
            message_ts="1234567890.123456",
            text="Test announcement"
        )
        self.db.add(ann)
        self.db.commit()
        self.db.refresh(ann)
        
        # Create target
        tgt = Target(
            announcement_id=ann.id,
            user_id="U67890"
        )
        self.db.add(tgt)
        self.db.commit()
        self.db.refresh(tgt)
        
        # Test the reminder function directly
        from .scheduler import send_reminder
        send_reminder(ann.id, tgt.id, tgt.user_id)
        
        # Verify that the Slack client was called
        mock_client.chat_postMessage.assert_called_once()
        args, kwargs = mock_client.chat_postMessage.call_args
        self.assertEqual(kwargs['channel'], "U67890")
        self.assertIn("Test announcement", kwargs['text'])

if __name__ == "__main__":
    unittest.main()
