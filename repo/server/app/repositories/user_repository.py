from sqlalchemy.orm import Session
from app.models.models import User, Role, RefreshToken, RevokedToken


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_username(self, username: str) -> User | None:
        return self.db.query(User).filter(User.username == username).first()

    def get_by_id(self, user_id: int) -> User | None:
        return self.db.query(User).filter(User.id == user_id).first()

    def get_role(self, role_name: str) -> Role | None:
        return self.db.query(Role).filter(Role.name == role_name).first()

    def get_role_by_id(self, role_id: int) -> Role | None:
        return self.db.query(Role).filter(Role.id == role_id).first()

    def create_user(self, username: str, password_hash: str, role_id: int, *, id_number: str | None = None, phone_number: str | None = None, email: str | None = None) -> User:
        user = User(
            username=username,
            password_hash=password_hash,
            role_id=role_id,
            id_number=id_number,
            phone_number=phone_number,
            email=email
        )
        self.db.add(user)
        self.db.flush()
        return user

    def save_refresh(self, user_id: int, token_hash: str, family_id: str, expires_at):
        token = RefreshToken(user_id=user_id, token_hash=token_hash, family_id=family_id, expires_at=expires_at)
        self.db.add(token)
        return token

    def get_refresh(self, hashed: str) -> RefreshToken | None:
        return self.db.query(RefreshToken).filter(RefreshToken.token_hash == hashed).first()

    def revoke_family(self, family_id: str):
        tokens = self.db.query(RefreshToken).filter(RefreshToken.family_id == family_id).all()
        for token in tokens:
            token.is_revoked = True

    def revoke_jti(self, jti: str):
        self.db.add(RevokedToken(jti=jti))

    def is_jti_revoked(self, jti: str) -> bool:
        return self.db.query(RevokedToken).filter(RevokedToken.jti == jti).first() is not None
