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

# Presença opcional da lib para demonstrar uso (mock, sem chamadas externas)
try:  # pragma: no cover - apenas para demonstração de uso
    from fastapi_keycloak import FastAPIKeycloak  # type: ignore
except Exception:  # pragma: no cover
    FastAPIKeycloak = None  # type: ignore

from .config import settings

# Esquema Bearer (não falha automaticamente para retornarmos 401 customizado)
bearer_scheme = HTTPBearer(auto_error=False)


def create_access_token(sub: str, role: str, expires_minutes: Optional[int] = None) -> str:
    """
    Gera um token JWT contendo o `sub` (identificador do usuário) e a `role`.

    Além do mock local, adicionamos claims no formato do Keycloak para
    demonstrar compatibilidade e uso da biblioteca `fastapi-keycloak` em modo mock:
    - `iss`, `aud`, `preferred_username`
    - `realm_access.roles` e `resource_access[client_id].roles`

    - `expires_minutes`: permite sobrescrever o TTL padrão definido nas configurações.
    - `iat`/`exp`: timestamps em segundos UTC.
    """
    now = datetime.now(timezone.utc)
    exp = now + timedelta(minutes=expires_minutes or settings.JWT_EXPIRES_MINUTES)
    payload = {
        "sub": sub,
        "role": role,  # ainda mantemos para retrocompatibilidade interna
        "preferred_username": sub,
        "iss": settings.KEYCLOAK_MOCK_ISSUER,
        "aud": settings.KEYCLOAK_MOCK_CLIENT_ID,
        "realm_access": {"roles": [role]},
        "resource_access": {settings.KEYCLOAK_MOCK_CLIENT_ID: {"roles": [role]}},
        "iat": int(now.timestamp()),  # emitido em
        "exp": int(exp.timestamp()),  # expira em
    }
    # Nota: HS256 com segredo local (mock). Em prod: use chave assimétrica do IdP (RS256/ES256).
    token = jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")
    return token


# Nota: a biblioteca `fastapi-keycloak` está presente como dependência para futura integração real.
# Neste modo MOCK, não instanciamos clientes que façam chamadas externas.
keycloak_mock = None  # placeholder intencional (sem I/O)


def decode_token(token: str) -> dict:
    """Valida e decodifica o token JWT. Lança 401 em caso de expiração ou token inválido.

    Observação: desabilitamos a verificação de `aud` no modo MOCK para aceitar tokens
    com claim `aud` no formato Keycloak sem precisar configurar audiência.
    """
    try:
        return jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=["HS256"],  # type: ignore
            options={"verify_aud": False},
        )
    except jwt.ExpiredSignatureError:  # type: ignore
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expirado")
    except jwt.InvalidTokenError:  # type: ignore
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")


async def get_current_user(creds: HTTPAuthorizationCredentials = Depends(bearer_scheme)) -> dict:
    """
    Extrai o token do header `Authorization: Bearer <token>` e retorna o payload decodificado.
    Se as claims `realm_access.roles` estiverem presentes (formato Keycloak), mapeia para `role` quando ausente.
    """
    if creds is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciais ausentes")
    token = creds.credentials
    payload = decode_token(token)

    # Compatibilidade: se `role` não vier, usar primeira role do realm_access
    if "role" not in payload:
        role = None
        try:
            roles = payload.get("realm_access", {}).get("roles", [])
            if roles:
                role = roles[0]
        except Exception:
            role = None
        if role:
            payload["role"] = role

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
