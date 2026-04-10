"""Seed the database with demo data for local development."""
import asyncio
import uuid
import hashlib
import numpy as np
from datetime import datetime, timezone
from sqlalchemy import select, text
from app.core.database import engine, async_session, Base
from app.core.auth import hash_password
from app.core.config import get_settings
from app.models.models import (
    AdminUser, Source, Document, Chunk, OfficeContact, FAQEntry,
    SourceCategory, DocumentStatus, ContentType, Audience,
)

settings = get_settings()


def mock_embedding(text: str) -> list[float]:
    seed = int(hashlib.md5(text.encode()).hexdigest()[:8], 16) % (2**31)
    rng = np.random.RandomState(seed)
    vec = rng.randn(settings.embedding_dimensions).astype(float)
    return (vec / np.linalg.norm(vec)).tolist()


OFFICES = [
    {"name": "Office of Admissions", "office_key": "admissions", "description": "Undergraduate admissions and recruitment", "phone": "(631) 632-6868", "email": "enroll@stonybrook.edu", "url": "https://www.stonybrook.edu/admissions/", "location": "118 Administration Building", "hours": "Mon-Fri 8:30am-5:00pm", "category": "admissions"},
    {"name": "Graduate School", "office_key": "graduate_admissions", "description": "Graduate admissions and programs", "phone": "(631) 632-4723", "email": "graduateadmissions@stonybrook.edu", "url": "https://www.stonybrook.edu/graduate-admissions/", "location": "2401 Computer Science Building", "hours": "Mon-Fri 8:30am-5:00pm", "category": "admissions"},
    {"name": "Office of the Registrar", "office_key": "registrar", "description": "Registration, transcripts, and academic records", "phone": "(631) 632-6175", "email": "registrar@stonybrook.edu", "url": "https://www.stonybrook.edu/registrar/", "location": "276 Administration Building", "hours": "Mon-Fri 8:30am-4:00pm", "category": "registrar"},
    {"name": "Student Financial Services (Bursar)", "office_key": "bursar", "description": "Tuition billing, payments, and refunds", "phone": "(631) 632-9316", "email": "bursar@stonybrook.edu", "url": "https://www.stonybrook.edu/bursar/", "location": "180 Administration Building", "hours": "Mon-Fri 8:30am-4:00pm", "category": "bursar"},
    {"name": "Financial Aid Office", "office_key": "financial_aid", "description": "Scholarships, grants, loans, and work-study", "phone": "(631) 632-6840", "email": "finaid@stonybrook.edu", "url": "https://www.stonybrook.edu/financial-aid/", "location": "180 Administration Building", "hours": "Mon-Fri 8:30am-4:00pm", "category": "financial_aid"},
    {"name": "Campus Residences", "office_key": "housing", "description": "On-campus housing and residential life", "phone": "(631) 632-6750", "email": "campus_residences@stonybrook.edu", "url": "https://www.stonybrook.edu/campus-residences/", "location": "Mendelsohn Quad Building A", "hours": "Mon-Fri 8:30am-5:00pm", "category": "housing"},
    {"name": "Campus Dining Services", "office_key": "dining", "description": "Meal plans and dining locations", "phone": "(631) 632-9400", "email": "fsa_dining@stonybrook.edu", "url": "https://www.stonybrook.edu/dining/", "location": "Student Activities Center", "hours": "Varies by location", "category": "dining"},
    {"name": "Visa and Immigration Services", "office_key": "international", "description": "International student support and immigration services", "phone": "(631) 632-4685", "email": "visa@stonybrook.edu", "url": "https://www.stonybrook.edu/commcms/visa/", "location": "E5320 Melville Library", "hours": "Mon-Fri 8:30am-4:00pm", "category": "student_affairs"},
    {"name": "Division of Information Technology", "office_key": "it_services", "description": "Technology services, NetID, and support", "phone": "(631) 632-9800", "email": "servicedesk@stonybrook.edu", "url": "https://it.stonybrook.edu/", "location": "Client Support Center, S-5410 Frank Melville Jr. Memorial Library", "hours": "Mon-Fri 8:00am-8:00pm", "category": "it_services"},
]

SOURCES = [
    {"name": "Undergraduate Admissions", "url": "https://www.stonybrook.edu/admissions/", "category": "admissions", "office": "admissions"},
    {"name": "Graduate Admissions", "url": "https://www.stonybrook.edu/graduate-admissions/", "category": "admissions", "office": "graduate_admissions"},
    {"name": "Registrar Information", "url": "https://www.stonybrook.edu/registrar/", "category": "registrar", "office": "registrar"},
    {"name": "Tuition and Billing", "url": "https://www.stonybrook.edu/bursar/tuition/", "category": "bursar", "office": "bursar"},
    {"name": "Financial Aid", "url": "https://www.stonybrook.edu/financial-aid/", "category": "financial_aid", "office": "financial_aid"},
    {"name": "Campus Housing", "url": "https://www.stonybrook.edu/campus-residences/", "category": "housing", "office": "housing"},
    {"name": "Dining Services", "url": "https://www.stonybrook.edu/dining/meal-plans/", "category": "dining", "office": "dining"},
    {"name": "Undergraduate Bulletin", "url": "https://www.stonybrook.edu/sb/bulletin/current/", "category": "academics", "office": None, "authority_score": 1.5},
]

DOCUMENTS_AND_CHUNKS = [
    {
        "title": "Undergraduate Admissions Overview",
        "source_key": 0,
        "url": "https://www.stonybrook.edu/admissions/freshman/",
        "chunks": [
            {"heading": "Application Requirements", "content": "Stony Brook University accepts applications through the Common Application and the SUNY Application. First-year applicants should submit their application by January 15 for priority consideration. Required materials include official high school transcripts, SAT or ACT scores (test-optional for recent cycles), a personal essay, and one letter of recommendation. The middle 50% SAT range for admitted students is 1310-1460. Stony Brook is a highly selective public research university and a member of the Association of American Universities (AAU)."},
            {"heading": "Application Deadlines", "content": "The priority application deadline for fall admission is January 15. Early Action decisions are typically released in mid-January. Regular Decision notifications are sent by April 1. Transfer students should apply by March 1 for fall admission and November 1 for spring admission. All deadlines are subject to change; please verify current dates on the admissions website."},
            {"heading": "Campus Visits", "content": "Prospective students can schedule campus tours and information sessions through the Office of Admissions. Tours are available Monday through Friday and select Saturdays during the academic year. Open House events are held in the fall for prospective students and their families. Virtual tour options are also available on the admissions website."},
        ],
    },
    {
        "title": "Tuition and Fees Schedule",
        "source_key": 3,
        "url": "https://www.stonybrook.edu/bursar/tuition/",
        "chunks": [
            {"heading": "Undergraduate Tuition", "content": "Tuition for full-time undergraduate New York State residents is approximately $7,070 per semester. Non-resident undergraduate tuition is approximately $12,980 per semester. Comprehensive fees including student activity fee, technology fee, transportation fee, and athletic fee total approximately $1,600 per semester. Total cost of attendance including room, board, books, and personal expenses is estimated at $29,000-$34,000 per year for NY residents. Tuition rates are set annually by the SUNY Board of Trustees and are subject to change."},
            {"heading": "Payment Options", "content": "The Bursar's Office offers several payment options including the Tuition Management Systems (TMS) monthly payment plan, which allows students to spread payments across the semester. Payment can be made online through SOLAR, by mail, or in person. Financial aid and scholarships are credited to student accounts approximately 10 days before the start of each semester. Students with outstanding balances may have registration holds placed on their accounts."},
        ],
    },
    {
        "title": "Campus Housing Guide",
        "source_key": 5,
        "url": "https://www.stonybrook.edu/campus-residences/halls/",
        "chunks": [
            {"heading": "Residential Communities", "content": "Stony Brook University offers housing in several residential quads and communities. Options include traditional corridor-style halls in Roosevelt Quad, suite-style living in Mendelsohn Quad, apartment-style units in Chapin Apartments and Schomburg Apartments, and the West Apartments complex. First-year students are guaranteed housing and are required to live on campus. Room rates vary by housing type, ranging from approximately $4,500 to $7,500 per semester."},
            {"heading": "Housing Application", "content": "Students can apply for housing through the MyHousing portal on the Campus Residences website. The housing application typically opens in March for the following fall semester. Room selection occurs in April based on lottery numbers. Students can indicate roommate preferences and building preferences in their application. All residential students are required to purchase a meal plan."},
        ],
    },
    {
        "title": "Financial Aid Information",
        "source_key": 4,
        "url": "https://www.stonybrook.edu/financial-aid/types/",
        "chunks": [
            {"heading": "Types of Aid", "content": "Stony Brook University offers various forms of financial aid including merit-based scholarships, need-based grants, federal and state loans, and work-study programs. The Presidential Scholarship covers full tuition for academically exceptional students. The Stony Brook Scholarship provides awards ranging from $1,000 to $12,000 per year based on academic achievement. Over 70% of Stony Brook students receive some form of financial assistance."},
            {"heading": "How to Apply", "content": "To apply for financial aid, students must complete the Free Application for Federal Student Aid (FAFSA) using school code 002838. The priority filing deadline is February 15 for the following academic year. New York State residents should also complete the TAP (Tuition Assistance Program) application. Students are automatically considered for university scholarships upon admission; no separate scholarship application is required for most merit awards."},
        ],
    },
    {
        "title": "Academic Registration",
        "source_key": 2,
        "url": "https://www.stonybrook.edu/registrar/registration/",
        "chunks": [
            {"heading": "Registration Process", "content": "Students register for courses through SOLAR (Student Online Access to Records). Registration periods open based on class standing, with seniors registering first. Each student must meet with their academic advisor to receive registration clearance before their enrollment window opens. Students can add or drop courses during the add/drop period in the first week of classes. After the add/drop period, course changes require instructor and department approval."},
            {"heading": "Transcripts", "content": "Official transcripts can be ordered through the National Student Clearinghouse or the Registrar's Office. Electronic transcripts are typically delivered within 1-2 business days. Paper transcripts take 3-5 business days to process. Current students can view their unofficial transcript for free through SOLAR. There is a fee of $10 per official transcript."},
        ],
    },
    {
        "title": "Meal Plans",
        "source_key": 6,
        "url": "https://www.stonybrook.edu/dining/meal-plans/",
        "chunks": [
            {"heading": "Residential Meal Plans", "content": "All residential students at Stony Brook are required to have a meal plan. Options include the Unlimited plan ($2,800/semester) with unlimited dining hall access, the 14-Meal plan ($2,600/semester) with 14 meals per week, and the 10-Meal plan ($2,400/semester) with 10 meals per week. Each plan includes Dining Dollars that can be used at retail dining locations across campus. The East Side Dining Center and Roth Food Court are the main dining facilities."},
        ],
    },
    {
        "title": "Graduate Programs Overview",
        "source_key": 1,
        "url": "https://www.stonybrook.edu/graduate-admissions/programs/",
        "chunks": [
            {"heading": "Graduate Programs", "content": "Stony Brook University offers over 100 master's programs, 40+ doctoral programs, and numerous graduate certificate programs across multiple schools and colleges. Notable programs include Computer Science, Applied Mathematics and Statistics, Biomedical Engineering, Physics, and the MBA program at the College of Business. The Graduate School oversees admissions, academic policies, and degree requirements for all graduate programs. Application requirements vary by program but generally include transcripts, GRE scores (some programs are GRE-optional), letters of recommendation, a statement of purpose, and a resume/CV."},
            {"heading": "Funding Opportunities", "content": "Graduate students may receive funding through teaching assistantships (TAs), research assistantships (RAs), graduate assistantships (GAs), and fellowships. Full funding packages for doctoral students typically include a tuition scholarship, a stipend, and health insurance. The Turner Fellowship and W. Burghardt Turner Fellowship are prestigious awards for underrepresented students. Funded doctoral students receive tuition waivers and competitive stipends that are reviewed annually."},
        ],
    },
]

FAQS = [
    {"question": "How do I apply to Stony Brook University?", "answer": "You can apply through the Common Application or the SUNY Application at stonybrook.edu/admissions. The priority deadline for fall admission is January 15. You'll need to submit your transcripts, test scores (optional), personal essay, and one letter of recommendation.", "category": "admissions", "office_key": "admissions", "priority": 10},
    {"question": "What is the tuition at Stony Brook?", "answer": "For full-time undergraduate NY residents, tuition is approximately $7,070 per semester. Non-residents pay approximately $12,980 per semester. Additional fees of about $1,600 per semester also apply. Visit stonybrook.edu/bursar for current rates.", "category": "bursar", "office_key": "bursar", "priority": 10},
    {"question": "How do I check my financial aid status?", "answer": "You can check your financial aid status through SOLAR (Student Online Access to Records) at solar.stonybrook.edu. Log in with your NetID and navigate to the Financial Aid section. For questions, contact the Financial Aid Office at (631) 632-6840.", "category": "financial_aid", "office_key": "financial_aid", "priority": 8},
    {"question": "How do I register for classes?", "answer": "Register through SOLAR at solar.stonybrook.edu during your assigned enrollment window. You must first obtain registration clearance from your academic advisor. Check your enrollment appointment date in SOLAR under the Registration tab.", "category": "registrar", "office_key": "registrar", "priority": 9},
    {"question": "How do I request an official transcript?", "answer": "Official transcripts can be ordered through the National Student Clearinghouse at www.getmytranscript.com or through the Registrar's Office. The cost is $10 per transcript. Electronic delivery takes 1-2 business days, paper delivery takes 3-5 business days.", "category": "registrar", "office_key": "registrar", "priority": 7},
    {"question": "What meal plans are available?", "answer": "Stony Brook offers three residential meal plans: Unlimited ($2,800/semester), 14-Meal ($2,600/semester), and 10-Meal ($2,400/semester). All residential students must have a meal plan. Each plan includes Dining Dollars for use at retail locations.", "category": "dining", "office_key": "dining", "priority": 6},
    {"question": "How do I apply for campus housing?", "answer": "Apply for housing through the MyHousing portal on the Campus Residences website. Applications typically open in March for the following fall. First-year students are guaranteed housing. Room selection occurs in April. Visit stonybrook.edu/campus-residences for details.", "category": "housing", "office_key": "housing", "priority": 7},
    {"question": "What scholarships does Stony Brook offer?", "answer": "Stony Brook offers merit-based scholarships including the Presidential Scholarship (full tuition) and Stony Brook Scholarship ($1,000-$12,000/year). Students are automatically considered upon admission. Over 70% of students receive some form of financial aid. Complete the FAFSA (code 002838) for need-based aid.", "category": "financial_aid", "office_key": "financial_aid", "priority": 9},
]


async def seed():
    async with async_session() as db:
        # Check if already seeded
        result = await db.execute(select(AdminUser))
        if result.scalar_one_or_none():
            print("Database already seeded. Skipping.")
            return

        print("Seeding database...")

        # Create admin user
        admin = AdminUser(
            email=settings.admin_default_email,
            password_hash=hash_password(settings.admin_default_password),
            name="Admin User",
            role="admin",
        )
        db.add(admin)
        print(f"  Created admin user: {settings.admin_default_email}")

        # Create office contacts
        for o in OFFICES:
            db.add(OfficeContact(**{k: SourceCategory(v) if k == "category" else v for k, v in o.items()}))
        print(f"  Created {len(OFFICES)} office contacts")

        # Create sources
        source_objects = []
        for s in SOURCES:
            src = Source(
                name=s["name"], url=s["url"],
                category=SourceCategory(s["category"]),
                office=s.get("office"),
                authority_score=s.get("authority_score", 1.0),
            )
            db.add(src)
            source_objects.append(src)
        await db.flush()
        print(f"  Created {len(SOURCES)} sources")

        # Create documents and chunks
        total_chunks = 0
        for doc_data in DOCUMENTS_AND_CHUNKS:
            source = source_objects[doc_data["source_key"]]
            content = "\n\n".join(c["content"] for c in doc_data["chunks"])
            doc = Document(
                source_id=source.id,
                title=doc_data["title"],
                source_url=doc_data["url"],
                content_type=ContentType.HTML,
                cleaned_content=content,
                content_hash=hashlib.sha256(content.encode()).hexdigest(),
                status=DocumentStatus.INDEXED,
                last_seen_at=datetime.now(timezone.utc),
            )
            db.add(doc)
            await db.flush()

            for i, chunk_data in enumerate(doc_data["chunks"]):
                chunk = Chunk(
                    document_id=doc.id,
                    chunk_index=i,
                    content=chunk_data["content"],
                    heading=chunk_data["heading"],
                    token_count=len(chunk_data["content"].split()),
                    embedding=mock_embedding(chunk_data["content"]),
                )
                db.add(chunk)
                total_chunks += 1

        print(f"  Created {len(DOCUMENTS_AND_CHUNKS)} documents with {total_chunks} chunks")

        # Create FAQs
        for f in FAQS:
            db.add(FAQEntry(
                question=f["question"], answer=f["answer"],
                category=SourceCategory(f["category"]),
                office_key=f.get("office_key"), priority=f.get("priority", 0),
            ))
        print(f"  Created {len(FAQS)} FAQ entries")

        await db.commit()
        print("Seeding complete!")


if __name__ == "__main__":
    asyncio.run(seed())
