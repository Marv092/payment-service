from fastapi import HTTPException, status, Security
from fastapi.security import APIKeyHeader

from app.config import settings

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

def validate_api_key(api_key: str = Security(api_key_header)) -> None:
    if api_key != settings.auth_api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Incorrect API key")