from datetime import datetime
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.license_key import LicenseKey
from app.models.license_key_redemption import LicenseKeyRedemption

BYPASS_ROLES = {"admin", "teacher"}   # មិនពាក់ព័ន្ធ License


def _is_expired(key: LicenseKey) -> bool:
    if key.status == "expired":
        return True
    # ផុតកំណត់តាមថ្ងៃ ទោះ status នៅ "active" (naive datetime ដូចកូដចាស់)
    return bool(key.expires_at and key.expires_at < datetime.now())


def get_license_access(db: Session, user: User) -> dict:
    roles = {r.name.lower() for r in user.roles}
    if roles & BYPASS_ROLES:
        return {"allowed": True, "code": None, "message": None, "expires_at": None}

    # Key ទាំងអស់ដែល user នេះធ្លាប់ Redeem (ថ្មីបំផុតមុន)
    keys = (
        db.query(LicenseKey)
        .join(LicenseKeyRedemption, LicenseKeyRedemption.license_key_id == LicenseKey.id)
        .filter(LicenseKeyRedemption.user_id == user.id)
        .order_by(LicenseKeyRedemption.id.desc())
        .all()
    )

    if not keys:
        return {"allowed": False, "code": "LICENSE_REQUIRED",
                "message": "You need a license key to use the calculator.", "expires_at": None}

    # មាន Key ត្រឹមត្រូវ ១ ក៏អនុញ្ញាតដែរ
    for key in keys:
        if key.status == "active" and not _is_expired(key):
            return {"allowed": True, "code": None, "message": None, "expires_at": key.expires_at}

    # គ្មាន Key ត្រឹមត្រូវ → ប្រើ Key ថ្មីបំផុតដើម្បីប្រាប់មូលហេតុ
    latest = keys[0]
    if latest.status == "revoked":
        code, message = "LICENSE_REVOKED", "Your license key has been revoked. Please contact your administrator."
    else:
        code, message = "LICENSE_EXPIRED", "Your license key has expired. Please enter a new key."
    return {"allowed": False, "code": code, "message": message, "expires_at": latest.expires_at}