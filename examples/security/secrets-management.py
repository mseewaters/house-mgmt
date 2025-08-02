# Secure secrets management
import os
import boto3
from functools import lru_cache

@lru_cache()
def get_jwt_secret() -> str:
    """Get JWT secret from environment or AWS Secrets Manager"""
    # Try environment variable first (local dev)
    jwt_secret = os.getenv("JWT_SECRET")
    if jwt_secret:
        return jwt_secret
    
    # Fallback to AWS Secrets Manager (production)
    try:
        secrets_client = boto3.client('secretsmanager')
        response = secrets_client.get_secret_value(SecretId="jwt-secret")
        return response["SecretString"]
    except Exception as e:
        raise RuntimeError(f"Failed to retrieve JWT secret: {e}")

@lru_cache()
def get_database_url() -> str:
    """Get database connection string"""
    db_url = os.getenv("DATABASE_URL")
    if db_url:
        return db_url
    
    # For DynamoDB, use AWS SDK defaults
    return "dynamodb://default"

# Usage examples:
# JWT_SECRET = get_jwt_secret()
# DB_URL = get_database_url()