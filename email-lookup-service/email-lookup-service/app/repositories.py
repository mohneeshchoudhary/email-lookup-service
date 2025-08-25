from .db import EmailRecord, SessionLocal
from sqlalchemy import select
from typing import Optional

class EmailRepo:
    @staticmethod
    async def get_by_key(key: str) -> Optional[EmailRecord]:
        async with SessionLocal() as session:
            res = await session.execute(select(EmailRecord).where(EmailRecord.key == key))
            return res.scalars().first()

    @staticmethod
    async def upsert(key: str, email: str | None, source: str | None) -> EmailRecord:
        async with SessionLocal() as session:
            rec = await session.get(EmailRecord, key)
            if rec is None:
                rec = EmailRecord(key=key, email=email, source=source)
                session.add(rec)
            else:
                rec.email = email
                rec.source = source
            await session.commit()
            await session.refresh(rec)
            return rec
