"""
Rotas de autenticação (mock).

- `POST /auth/login`: gera um JWT simples contendo `sub` e `role` informados.
- Em produção, este fluxo seria redirecionado para um IdP (ex.: Keycloak) e
  o backend apenas validaria o token recebido pelo frontend.
"""

from fastapi import APIRouter
from pydantic import BaseModel, Field

from ..security import create_access_token


class LoginRequest(BaseModel):
    # Usuário apenas identificador textual (mock)
    username: str = Field(..., min_length=1)
    # Role obrigatória dentre as suportadas
    role: str = Field(..., pattern=r"^(operador|admin|super_admin)$")


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


router = APIRouter()


@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest):
    """Cria e retorna um token de acesso para o par (username, role)."""
    token = create_access_token(sub=req.username, role=req.role)
    return TokenResponse(access_token=token)
