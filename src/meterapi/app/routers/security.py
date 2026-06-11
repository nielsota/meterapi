from typing import Annotated

from pydantic import BaseModel
from fastapi import Depends, APIRouter
from fastapi.security import OAuth2PasswordBearer

# oauth2_scheme is a callable that returns a string
# fastapi calls with the correct arguments to get the token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

router = APIRouter(tags=["security"])

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"

@router.get("/token", response_model=TokenResponse)
def get_token(token: Annotated[str, Depends(oauth2_scheme)]) -> TokenResponse:
    return TokenResponse(access_token=token)

# get_current_user flows like this:
# 1. authorization header contains username and password
# 2. that gets put in the Bearer token
# 3. oauth2_scheme extracts the token from the authorization header
# 4. that token is decoded into the username 
# 5. get_current_user returns the user
# 6. user is used to authenticate the request
