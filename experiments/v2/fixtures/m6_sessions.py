import hashlib
import hmac
import secrets
import time

SESSION_TTL = 3600


class SessionStore:
    def __init__(self, secret: bytes):
        self.secret = secret
        self.sessions = {}

    def _sign(self, session_id: str) -> str:
        mac = hmac.new(self.secret, session_id.encode(), hashlib.sha256).hexdigest()
        return f"{session_id}.{mac}"

    def create(self, user_id: str) -> str:
        session_id = secrets.token_urlsafe(32)
        self.sessions[session_id] = {"user_id": user_id, "created": time.time()}
        return self._sign(session_id)

    def _verify(self, token: str):
        session_id, _, mac = token.rpartition(".")
        expected = hmac.new(self.secret, session_id.encode(), hashlib.sha256).hexdigest()
        if mac != expected:
            return None
        return session_id

    def get_user(self, token: str):
        session_id = self._verify(token)
        if session_id is None:
            return None
        session = self.sessions.get(session_id)
        if session is None:
            return None
        if time.time() - session["created"] > SESSION_TTL:
            del self.sessions[session_id]
            return None
        return session["user_id"]

    def destroy(self, token: str) -> None:
        session_id = self._verify(token)
        if session_id is not None:
            self.sessions.pop(session_id, None)

    def destroy_all_for(self, user_id: str) -> int:
        doomed = [sid for sid, s in self.sessions.items() if s["user_id"] == user_id]
        for sid in doomed:
            del self.sessions[sid]
        return len(doomed)


def hash_password(password: str, salt: bytes = None) -> tuple:
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.sha256(salt + password.encode()).hexdigest()
    return salt, digest


def check_password(password: str, salt: bytes, digest: str) -> bool:
    return hmac.compare_digest(hash_password(password, salt)[1], digest)
