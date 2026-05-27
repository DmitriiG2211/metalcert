"""
Seed script: creates admin user + sample certificates for testing.
Run: python seed_data.py
"""
import asyncio
from datetime import date
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.core.security import get_password_hash
from app.models.user import User, UserRole
from app.models.certificate import Certificate, CertificateStatus


SAMPLE_CERTIFICATES = [
    {
        "original_filename": "cert_truba_prof_120x120x4.pdf",
        "file_type": "application/pdf",
        "file_hash": "aabbcc001",
        "product_type": "РўСЂСѓР±Р° РїСЂРѕС„РёР»СЊРЅР°СЏ",
        "dimensions": "120С…120С…4",
        "material": "РЎС‚3СЃРї",
        "gost": "Р“РћРЎРў 8639-82",
        "normalized_product_name": "РўСЂСѓР±Р° РїСЂРѕС„РёР»СЊРЅР°СЏ 120С…120С…4 РЎС‚3СЃРї Р“РћРЎРў 8639-82",
        "certificate_number": "РљР§-2024-00145",
        "certificate_date": date(2024, 3, 15),
        "manufacturer": "РћРћРћ В«РњРµС‚Р°Р»Р»-РЎРµСЂРІРёСЃВ»",
        "ocr_confidence": 0.92,
        "status": CertificateStatus.parsed,
    },
    {
        "original_filename": "cert_list_09g2s.pdf",
        "file_type": "application/pdf",
        "file_hash": "aabbcc002",
        "product_type": "Р›РёСЃС‚",
        "dimensions": "3 РјРј",
        "material": "09Р“2РЎ",
        "gost": "Р“РћРЎРў 19903-2015",
        "normalized_product_name": "Р›РёСЃС‚ 3 РјРј 09Р“2РЎ Р“РћРЎРў 19903-2015",
        "certificate_number": "РЎРљ-2024-00089",
        "certificate_date": date(2024, 1, 20),
        "manufacturer": "РџРђРћ В«РќР›РњРљВ»",
        "ocr_confidence": 0.95,
        "status": CertificateStatus.parsed,
    },
    {
        "original_filename": "cert_armatura_a500c_12.jpg",
        "file_type": "image/jpeg",
        "file_hash": "aabbcc003",
        "product_type": "РђСЂРјР°С‚СѓСЂР°",
        "dimensions": "12 РјРј",
        "material": "Рђ500РЎ",
        "gost": "Р“РћРЎРў Р  52544-2006",
        "normalized_product_name": "РђСЂРјР°С‚СѓСЂР° 12 РјРј Рђ500РЎ Р“РћРЎРў Р  52544-2006",
        "certificate_number": "РђРњ-2024-0552",
        "certificate_date": date(2024, 2, 5),
        "manufacturer": "РћРђРћ В«РњРњРљВ»",
        "batch_number": "Рџ-2024-115",
        "heat_number": "Р“-44512",
        "ocr_confidence": 0.88,
        "status": CertificateStatus.parsed,
    },
    {
        "original_filename": "cert_shveller_16p.pdf",
        "file_type": "application/pdf",
        "file_hash": "aabbcc004",
        "product_type": "РЁРІРµР»Р»РµСЂ",
        "dimensions": "16Рџ",
        "material": "РЎС‚3СЃРї",
        "gost": "Р“РћРЎРў 8240-97",
        "normalized_product_name": "РЁРІРµР»Р»РµСЂ 16Рџ РЎС‚3СЃРї Р“РћРЎРў 8240-97",
        "certificate_number": "РЁ-2024-0221",
        "certificate_date": date(2024, 4, 10),
        "manufacturer": "Р—РђРћ В«РЎРµРІРµСЂСЃС‚Р°Р»СЊ-РњРµС‚РёР·В»",
        "ocr_confidence": 0.91,
        "status": CertificateStatus.parsed,
    },
    {
        "original_filename": "cert_ugolok_50x50x5.pdf",
        "file_type": "application/pdf",
        "file_hash": "aabbcc005",
        "product_type": "РЈРіРѕР»РѕРє",
        "dimensions": "50С…50С…5",
        "material": "РЎ255",
        "gost": "Р“РћРЎРў 8509-93",
        "normalized_product_name": "РЈРіРѕР»РѕРє 50С…50С…5 РЎ255 Р“РћРЎРў 8509-93",
        "certificate_number": "РЈР“-2024-0089",
        "certificate_date": date(2024, 3, 28),
        "manufacturer": "РћРђРћ В«Р•РІСЂР°Р· Р—РЎРњРљВ»",
        "ocr_confidence": 0.89,
        "status": CertificateStatus.parsed,
    },
    {
        "original_filename": "cert_krug_20_st45.pdf",
        "file_type": "application/pdf",
        "file_hash": "aabbcc006",
        "product_type": "РљСЂСѓРі",
        "dimensions": "20 РјРј",
        "material": "РЎС‚45",
        "gost": "Р“РћРЎРў 2590-2006",
        "normalized_product_name": "РљСЂСѓРі 20 РјРј РЎС‚45 Р“РћРЎРў 2590-2006",
        "certificate_number": "РљР -2024-0341",
        "certificate_date": date(2024, 5, 2),
        "manufacturer": "РћРђРћ В«Р§РњРљВ»",
        "heat_number": "Р“-55231",
        "ocr_confidence": 0.94,
        "status": CertificateStatus.parsed,
    },
    {
        "original_filename": "cert_balka_20b1.pdf",
        "file_type": "application/pdf",
        "file_hash": "aabbcc007",
        "product_type": "Р‘Р°Р»РєР°",
        "dimensions": "20Р‘1",
        "material": "РЎС‚3",
        "gost": "Р“РћРЎРў 26020-83",
        "normalized_product_name": "Р‘Р°Р»РєР° 20Р‘1 РЎС‚3 Р“РћРЎРў 26020-83",
        "certificate_number": "Р‘Р›-2024-0112",
        "certificate_date": date(2024, 1, 15),
        "manufacturer": "РџРђРћ В«РЎРµРІРµСЂСЃС‚Р°Р»СЊВ»",
        "ocr_confidence": 0.87,
        "status": CertificateStatus.parsed,
    },
    {
        "original_filename": "cert_truba_vgp_25x3.pdf",
        "file_type": "application/pdf",
        "file_hash": "aabbcc008",
        "product_type": "РўСЂСѓР±Р° Р’РіРї",
        "dimensions": "25С…3,2",
        "material": "РЎС‚3",
        "gost": "Р“РћРЎРў 3262-75",
        "normalized_product_name": "РўСЂСѓР±Р° Р’Р“Рџ 25С…3,2 РЎС‚3 Р“РћРЎРў 3262-75",
        "certificate_number": "Р’Р“Рџ-2024-0678",
        "certificate_date": date(2024, 4, 20),
        "manufacturer": "РћРћРћ В«РўСЂСѓР±РЅС‹Р№ Р—Р°РІРѕРґВ»",
        "ocr_confidence": 0.90,
        "status": CertificateStatus.parsed,
    },
    {
        "original_filename": "cert_truba_esv_76x3.5.jpg",
        "file_type": "image/jpeg",
        "file_hash": "aabbcc009",
        "product_type": "РўСЂСѓР±Р° Р­Р»РµРєС‚СЂРѕСЃРІР°СЂРЅР°СЏ",
        "dimensions": "76С…3,5",
        "material": "РЎС‚3",
        "gost": "Р“РћРЎРў 10704-91",
        "normalized_product_name": "РўСЂСѓР±Р° СЌР»РµРєС‚СЂРѕСЃРІР°СЂРЅР°СЏ 76С…3,5 РЎС‚3 Р“РћРЎРў 10704-91",
        "certificate_number": "Р­РЎ-2024-0445",
        "certificate_date": date(2024, 2, 28),
        "manufacturer": "РћРђРћ В«Р’РњР—В»",
        "ocr_confidence": 0.78,
        "status": CertificateStatus.needs_review,
    },
    {
        "original_filename": "scan_unknown_cert.png",
        "file_type": "image/png",
        "file_hash": "aabbcc010",
        "product_type": None,
        "normalized_product_name": None,
        "ocr_confidence": 0.45,
        "status": CertificateStatus.needs_review,
        "extracted_text": "РќРµС‡РёС‚Р°РµРјС‹Р№ СЃРµСЂС‚РёС„РёРєР°С‚, С‚СЂРµР±СѓРµС‚ СЂСѓС‡РЅРѕР№ РѕР±СЂР°Р±РѕС‚РєРё",
    },
]


async def main():
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # Create admin user
        from sqlalchemy import select
        result = await session.execute(select(User).where(User.email == "admin@example.com"))
        admin = result.scalar_one_or_none()
        if not admin:
            admin = User(
                email="admin@example.com",
                password_hash=get_password_hash("admin123"),
                role=UserRole.admin,
            )
            session.add(admin)
            print("Created admin user: admin@example.com / admin123")

        manager = User(
            email="manager@example.com",
            password_hash=get_password_hash("manager123"),
            role=UserRole.manager,
        )
        session.add(manager)
        print("Created manager user: manager@example.com / manager123")

        viewer = User(
            email="viewer@example.com",
            password_hash=get_password_hash("viewer123"),
            role=UserRole.viewer,
        )
        session.add(viewer)
        print("Created viewer user: viewer@example.com / viewer123")

        # Create certificates
        for data in SAMPLE_CERTIFICATES:
            cert = Certificate(**data)
            session.add(cert)
        print(f"Created {len(SAMPLE_CERTIFICATES)} sample certificates")

        await session.commit()

    await engine.dispose()
    print("Seed data inserted successfully!")


if __name__ == "__main__":
    asyncio.run(main())


