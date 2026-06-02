"""
Utilitários de segurança (autenticação e autorização) da API.

- Autenticação: tokens JWT simples assinados com HS256 (mock para ambiente local).
- Autorização: verificação de role mínima via dependência do FastAPI.

Em produção, troque o segredo (`JWT_SECRET`) e integre com um provedor OIDC (ex.: Keycloak),
validando a assinatura pública do IdP e as `claims` obrigatórias.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .config import settings

# Esquema Bearer (não falha automaticamente para retornarmos 401 customizado)
bearer_scheme = HTTPBearer(auto_error=False)


def create_access_token(sub: str, role: str, expires_minutes: Optional[int] = None) -> str:
    """
    Gera um token JWT contendo o `sub` (identificador do usuário) e a `role`.

    - `expires_minutes`: permite sobrescrever o TTL padrão definido nas configurações.
    - `iat`/`exp`: timestamps em segundos UTC.
    """
    now = datetime.now(timezone.utc)
    exp = now + timedelta(minutes=expires_minutes or settings.JWT_EXPIRES_MINUTES)
    payload = {
        "sub": sub,
        "role": role,
        "iat": int(now.timestamp()),  # emitido em
        "exp": int(exp.timestamp()),  # expira em
    }
    # Nota: HS256 com segredo local (mock). Em prod: use chave assimétrica do IdP (RS256/ES256).
    token = jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")
    return token


def decode_token(token: str) -> dict:
    """Valida e decodifica o token JWT. Lança 401 em caso de expiração ou token inválido."""
    try:
        return jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])  # type: ignore
    except jwt.ExpiredSignatureError:  # type: ignore
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expirado")
    except jwt.InvalidTokenError:  # type: ignore
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")


async def get_current_user(creds: HTTPAuthorizationCredentials = Depends(bearer_scheme)) -> dict:
    """
    Extrai o token do header `Authorization: Bearer <token>` e retorna o payload decodificado.
    """
    if creds is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciais ausentes")
    token = creds.credentials
    payload = decode_token(token)
    return payload


def require_role(min_role: str):
    """
    Dependência de autorização baseada em hierarquia de roles.

    Ex.: `Depends(require_role("admin"))` permite `admin` e `super_admin`,
    mas bloqueia `operador`.
    """
    order = {"operador": 1, "admin": 2, "super_admin": 3}

    async def dependency(user: dict = Depends(get_current_user)):
        user_role = user.get("role")
        if user_role not in order:
            raise HTTPException(status_code=403, detail="Role inválida")
        if order[user_role] < order[min_role]:
            raise HTTPException(status_code=403, detail="Permissão insuficiente")
        return user

    return dependency
