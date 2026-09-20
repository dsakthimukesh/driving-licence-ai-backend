import uuid
import unittest
from datetime import datetime, timezone
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.main import app
from app.core.database import Base, get_db
from app.core.security import create_access_token
from app.models.user import User
from app.models.document import Document
from app.models.document_info import DocumentInfo
from app.repositories import document_repository


class TestDocumentSecurityAndOwnership(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool
        )

        @event.listens_for(cls.engine, "connect")
        def attach_public_schema(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("ATTACH DATABASE ':memory:' AS public")
            cursor.close()

        Base.metadata.create_all(bind=cls.engine)
        cls.TestingSession = sessionmaker(bind=cls.engine)

        def override_get_db():
            db = cls.TestingSession()
            try:
                yield db
            finally:
                db.close()

        app.dependency_overrides[get_db] = override_get_db
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        app.dependency_overrides.clear()

    def setUp(self):
        self.db = self.TestingSession()
        now = datetime.now(timezone.utc)

        suffix = str(uuid.uuid4())[:8]
        # Create User A
        self.user_a_id = uuid.uuid4()
        self.user_a = User(
            user_id=self.user_a_id,
            name="User A",
            email=f"usera_{suffix}@example.com",
            hashed_password="hashed_pw_a",
            created_date=now,
            last_modified_date=now
        )
        self.db.add(self.user_a)

        # Create User B
        self.user_b_id = uuid.uuid4()
        self.user_b = User(
            user_id=self.user_b_id,
            name="User B",
            email=f"userb_{suffix}@example.com",
            hashed_password="hashed_pw_b",
            created_date=now,
            last_modified_date=now
        )
        self.db.add(self.user_b)
        self.db.commit()

        # Create Document owned by User B
        self.doc_b_id = uuid.uuid4()
        self.doc_b = Document(
            document_id=self.doc_b_id,
            user_id=self.user_b_id,
            file_name="user_b_licence.pdf",
            bucket_name="documents",
            storage_path=f"{self.user_b_id}/{self.doc_b_id}/user_b_licence.pdf",
            status="COMPLETED",
            created_by=self.user_b_id,
            created_date=now,
            last_modified_by=self.user_b_id,
            last_modified_date=now
        )
        self.db.add(self.doc_b)
        self.db.commit()

        # Create DocumentInfo for User B's document
        self.doc_info_b = DocumentInfo(
            document_info_id=uuid.uuid4(),
            document_id=self.doc_b_id,
            licence_number="MH1220190001234",
            full_name="ROHAN ANIL DESHMUKH",
            parent_name="ANIL VASANT DESHMUKH",
            address="Pune, Maharashtra",
            created_by=self.user_b_id,
            created_date=now,
            last_modified_by=f"userb_{suffix}@example.com",
            last_modified_date=now
        )
        self.db.add(self.doc_info_b)
        self.db.commit()

        # Generate tokens
        self.token_a = create_access_token({"sub": str(self.user_a_id)})
        self.headers_a = {"Authorization": f"Bearer {self.token_a}"}

        self.token_b = create_access_token({"sub": str(self.user_b_id)})
        self.headers_b = {"Authorization": f"Bearer {self.token_b}"}

    def tearDown(self):
        self.db.query(DocumentInfo).delete()
        self.db.query(Document).delete()
        self.db.query(User).delete()
        self.db.commit()
        self.db.close()

    def test_unauthenticated_requests(self):
        """Verify unauthenticated requests return 401 Unauthorized for all document endpoints."""
        endpoints = [
            ("GET", "/api/v1/documents"),
            ("GET", f"/api/v1/documents/{self.doc_b_id}"),
            ("POST", "/api/v1/documents/upload-url"),
            ("POST", f"/api/v1/documents/{self.doc_b_id}/confirm-upload"),
            ("POST", f"/api/v1/documents/{self.doc_b_id}/process"),
            ("GET", f"/api/v1/documents/{self.doc_b_id}/download-url"),
            ("GET", f"/api/v1/documents/{self.doc_b_id}/info"),
            ("POST", f"/api/v1/documents/{self.doc_b_id}/retrieve"),
            ("POST", f"/api/v1/documents/{self.doc_b_id}/ask"),
            ("DELETE", f"/api/v1/documents/{self.doc_b_id}"),
        ]

        for method, url in endpoints:
            if method == "GET":
                res = self.client.get(url)
            elif method == "POST":
                res = self.client.post(url, json={"question": "test"})
            elif method == "DELETE":
                res = self.client.delete(url)
            self.assertEqual(res.status_code, 401, f"Expected 401 for unauthenticated {method} {url}, got {res.status_code}")

    def test_user_a_accessing_user_b_document_details(self):
        """User A accessing User B's document details returns 404 Not Found."""
        res = self.client.get(f"/api/v1/documents/{self.doc_b_id}", headers=self.headers_a)
        self.assertEqual(res.status_code, 404)
        self.assertEqual(res.json().get("detail"), "Document not found")

    def test_user_a_generating_user_b_download_url(self):
        """User A generating download URL for User B's document returns 404 Not Found."""
        res = self.client.get(f"/api/v1/documents/{self.doc_b_id}/download-url", headers=self.headers_a)
        self.assertEqual(res.status_code, 404)

    def test_user_a_confirming_user_b_upload(self):
        """User A confirming upload for User B's document returns 404 Not Found."""
        res = self.client.post(f"/api/v1/documents/{self.doc_b_id}/confirm-upload", headers=self.headers_a)
        self.assertEqual(res.status_code, 404)

    def test_user_a_getting_user_b_document_info(self):
        """User A fetching structured info for User B's document returns 404 Not Found."""
        res = self.client.get(f"/api/v1/documents/{self.doc_b_id}/info", headers=self.headers_a)
        self.assertEqual(res.status_code, 404)

    def test_user_a_processing_user_b_document(self):
        """User A processing User B's document returns 404 Not Found."""
        res = self.client.post(f"/api/v1/documents/{self.doc_b_id}/process", headers=self.headers_a)
        self.assertEqual(res.status_code, 404)

    def test_user_a_retrieving_user_b_chunks(self):
        """User A retrieving chunks of User B's document returns 404 Not Found."""
        res = self.client.post(
            f"/api/v1/documents/{self.doc_b_id}/retrieve",
            headers=self.headers_a,
            json={"question": "What is the licence number?", "top_k": 3}
        )
        self.assertEqual(res.status_code, 404)

    def test_user_a_asking_question_on_user_b_document(self):
        """User A asking question on User B's document returns 404 Not Found."""
        res = self.client.post(
            f"/api/v1/documents/{self.doc_b_id}/ask",
            headers=self.headers_a,
            json={"question": "What is the licence number?", "top_k": 3}
        )
        self.assertEqual(res.status_code, 404)

    def test_user_a_deleting_user_b_document(self):
        """User A attempting to delete User B's document returns 404 Not Found and does NOT delete User B's document."""
        res = self.client.delete(f"/api/v1/documents/{self.doc_b_id}", headers=self.headers_a)
        self.assertEqual(res.status_code, 404)

        # Verify Document B still exists in database
        doc_still_exists = document_repository.get_document_by_id(db=self.db, document_id=self.doc_b_id)
        self.assertIsNotNone(doc_still_exists)
        self.assertEqual(doc_still_exists.user_id, self.user_b_id)

    def test_user_b_can_access_own_document(self):
        """User B can successfully access their own document."""
        res = self.client.get(f"/api/v1/documents/{self.doc_b_id}", headers=self.headers_b)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["document_id"], str(self.doc_b_id))
        self.assertEqual(data["file_name"], "user_b_licence.pdf")


if __name__ == "__main__":
    unittest.main()
