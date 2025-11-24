"""
Pytest configuration and fixtures.
"""
import asyncio
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from httpx import AsyncClient

from app.config import get_settings
from app.database import db
from app.main import app

settings = get_settings()


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def test_db():
    """Database fixture for tests."""
    # Use test database URL
    test_db_url = settings.database_url.replace("/compliance", "/compliance_test")

    # Connect
    await db.connect()

    yield db

    # Cleanup and disconnect
    await db.disconnect()


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Test client fixture."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def admin_headers():
    """Admin API key headers."""
    return {"X-API-Key": settings.admin_api_key}


@pytest.fixture
def mock_github_webhook_headers():
    """Mock GitHub webhook headers."""
    return {
        "X-GitHub-Event": "push",
        "X-GitHub-Delivery": "test-delivery-id",
        "X-Hub-Signature-256": "sha256=test-signature",
        "Content-Type": "application/json",
    }


@pytest.fixture
def sample_code_python():
    """Sample Python code for testing."""
    return '''
def calculate_interest(principal, rate, time):
    """Calculate simple interest."""
    if principal <= 0 or rate <= 0 or time <= 0:
        raise ValueError("All values must be positive")
    
    interest = (principal * rate * time) / 100
    return interest

class BankAccount:
    def __init__(self, account_number, balance=0):
        self.account_number = account_number
        self.balance = balance
    
    def deposit(self, amount):
        if amount <= 0:
            raise ValueError("Deposit amount must be positive")
        self.balance += amount
        return self.balance
    
    def withdraw(self, amount):
        if amount > self.balance:
            raise ValueError("Insufficient funds")
        self.balance -= amount
        return self.balance
'''


@pytest.fixture
def sample_code_javascript():
    """Sample JavaScript code for testing."""
    return '''
function validateEmail(email) {
    const emailRegex = /^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$/;
    return emailRegex.test(email);
}

class PaymentProcessor {
    constructor(apiKey) {
        this.apiKey = apiKey;
        this.baseUrl = 'https://api.payment.com';
    }
    
    async processPayment(amount, currency) {
        const response = await fetch(`${this.baseUrl}/charge`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${this.apiKey}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ amount, currency })
        });
        
        return response.json();
    }
}
'''


@pytest.fixture
def sample_regulation_chunk():
    """Sample regulation chunk for testing."""
    return {
        "rule_id": "RBI_KYC_2024",
        "rule_section": "Section 4.2.1",
        "source_document": "RBI Master Direction on KYC",
        "chunk_text": "All financial institutions must implement multi-factor authentication "
        "for customer accounts. Authentication must include at least two of: "
        "something the user knows (password), something the user has (token), "
        "or something the user is (biometric).",
        "chunk_index": 0,
        "metadata": {"category": "authentication", "severity": "critical"},
    }

