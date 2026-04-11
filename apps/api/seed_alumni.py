"""
Seed script: create 20 dummy SBU alumni with varied profiles.
Run inside the api container:
  docker compose exec api python seed_alumni.py
"""
import asyncio
import random
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

from app.core.config import get_settings
from app.core.auth import hash_password
from app.models.models import AlumniUser, AlumniProfile
from app.services.ai_providers import get_embedding_provider

settings = get_settings()

ALUMNI = [
    # (name, email, degree, major, grad_year, company, title, industry, location, skills, interests, open_to, bio, is_international, linkedin)
    ("Alex Chen",       "alex.chen@alumni.stonybrook.edu",    "ms",  "Computer Science",         2021, "Google",         "Software Engineer",            "Tech",              "Mountain View, CA",  ["Python","Go","Kubernetes","GCP"],               ["Cloud","Open Source","Hiking"],         ["mentoring","coffee_chat","referrals_career_advice"],    "SBU MS CS grad working on Google Cloud infra.",               False, "https://linkedin.com/in/alexchen"),
    ("Priya Patel",     "priya.patel@alumni.stonybrook.edu",  "phd", "Applied Math",             2019, "Two Sigma",      "Quantitative Researcher",      "Finance",           "New York, NY",       ["Python","C++","Statistics","ML"],               ["Quant Finance","Research","Chess"],     ["mentoring","research_project_collab"],                          "Quant researcher at Two Sigma. Love ML applications in finance.", True,  "https://linkedin.com/in/priyapatel"),
    ("Jordan Lee",      "jordan.lee@alumni.stonybrook.edu",   "bs",  "Computer Science",         2023, "Meta",           "Software Engineer",            "Tech",              "Menlo Park, CA",     ["React","TypeScript","GraphQL","Python"],         ["Web Dev","Gaming","Music"],             ["coffee_chat","community_general_chat"],                         "New grad at Meta on the Messenger team.",                     False, None),
    ("Sofia Rossi",     "sofia.rossi@alumni.stonybrook.edu",  "ms",  "Biomedical Engineering",   2020, "Pfizer",         "Research Scientist",           "Healthcare",        "New York, NY",       ["Python","R","CRISPR","Bioinformatics"],          ["Biotech","Healthcare","Cooking"],       ["research_project_collab","mentoring","events_networking"],      "Working on mRNA platform at Pfizer.",                         True,  "https://linkedin.com/in/sofiarossi"),
    ("Marcus Johnson",  "marcus.j@alumni.stonybrook.edu",     "mba", "Business Administration",  2018, "McKinsey",       "Associate",                    "Consulting",        "Chicago, IL",        ["Excel","SQL","Strategy","PowerPoint"],           ["Entrepreneurship","Finance","Tennis"], ["referrals_career_advice","mentoring","coffee_chat"],            "MBA grad consulting for Fortune 500 clients.",                False, "https://linkedin.com/in/marcusjohnson"),
    ("Yuki Tanaka",     "yuki.tanaka@alumni.stonybrook.edu",  "ms",  "Electrical Engineering",   2022, "Qualcomm",       "IC Design Engineer",           "Tech",              "San Diego, CA",      ["Verilog","MATLAB","VLSI","Python"],              ["Hardware","Gaming","Anime"],            ["mentoring","research_project_collab","coffee_chat"],            "Chip designer at Qualcomm focused on 5G modems.",             True,  None),
    ("Emma Williams",   "emma.w@alumni.stonybrook.edu",       "ba",  "Economics",                2020, "Goldman Sachs",  "Analyst",                      "Finance",           "New York, NY",       ["Excel","Python","Bloomberg","SQL"],              ["Finance","Travel","Photography"],      ["coffee_chat","referrals_career_advice","events_networking"],    "Investment banking analyst on tech M&A.",                     False, "https://linkedin.com/in/emmawilliams"),
    ("Rahul Sharma",    "rahul.s@alumni.stonybrook.edu",      "ms",  "Computer Science",         2021, "Amazon",         "SDE II",                       "Tech",              "Seattle, WA",        ["Java","AWS","DynamoDB","Kotlin"],                ["Distributed Systems","Cricket","ML"],  ["mentoring","referrals_career_advice","coffee_chat"],            "Backend engineer at Amazon Stores.",                          True,  "https://linkedin.com/in/rahulsharma"),
    ("Claire Dubois",   "claire.d@alumni.stonybrook.edu",     "phd", "Chemistry",                2017, "BASF",           "Senior Researcher",            "Research/Academia", "Florham Park, NJ",   ["Python","MATLAB","Spectroscopy","ChemDraw"],     ["Green Chemistry","Cycling","Wine"],     ["research_project_collab","mentoring"],                          "PhD chemist working on sustainable materials.",               True,  None),
    ("Tyler Brooks",    "tyler.b@alumni.stonybrook.edu",      "bs",  "Computer Science",         2022, "Stripe",         "Software Engineer",            "Tech",              "San Francisco, CA",  ["Ruby","Python","React","Postgres"],              ["Fintech","Startups","Rock Climbing"],  ["coffee_chat","community_general_chat","events_networking"],     "Building payment infrastructure at Stripe.",                  False, "https://linkedin.com/in/tylerbrooks"),
    ("Aisha Khan",      "aisha.k@alumni.stonybrook.edu",      "ms",  "Data Science",             2022, "Netflix",        "Data Scientist",               "Tech",              "Los Gatos, CA",      ["Python","Spark","SQL","TensorFlow","R"],         ["Recommendation Systems","Reading","Yoga"], ["mentoring","research_project_collab","coffee_chat"],         "Working on content recommendation at Netflix.",               True,  "https://linkedin.com/in/aishakhan"),
    ("Kevin Park",      "kevin.p@alumni.stonybrook.edu",      "bs",  "Mechanical Engineering",   2019, "Tesla",          "Manufacturing Engineer",       "Tech",              "Fremont, CA",        ["CAD","Python","Lean","Six Sigma"],               ["EVs","Robotics","3D Printing"],         ["mentoring","events_networking"],                                "Working on Model Y production at Tesla Gigafactory.",         False, None),
    ("Nina Volkov",     "nina.v@alumni.stonybrook.edu",       "phd", "Computer Science",         2020, "MIT CSAIL",      "Postdoctoral Researcher",      "Research/Academia", "Cambridge, MA",      ["C++","CUDA","PyTorch","Computer Vision"],        ["AI Safety","Robotics","Piano"],         ["research_project_collab","mentoring"],                          "Researching embodied AI at MIT CSAIL.",                       True,  "https://linkedin.com/in/ninavolkov"),
    ("James O'Brien",   "james.ob@alumni.stonybrook.edu",     "ba",  "Political Science",        2015, "NYC Government", "Policy Analyst",               "Government",        "New York, NY",       ["Research","Writing","Data Analysis","Excel"],   ["Public Policy","Cycling","Jazz"],      ["coffee_chat","events_networking","community_general_chat"],     "Working on tech policy at NYC Mayor's office.",               False, None),
    ("Mei Lin",         "mei.lin@alumni.stonybrook.edu",      "ms",  "Computer Science",         2023, "Apple",          "iOS Engineer",                 "Tech",              "Cupertino, CA",      ["Swift","Objective-C","Xcode","Python"],          ["Mobile Dev","Design","Photography"],   ["coffee_chat","mentoring","referrals_career_advice"],            "iOS engineer on the Health app team at Apple.",               True,  "https://linkedin.com/in/meilin"),
    ("David Kim",       "david.kim@alumni.stonybrook.edu",    "ms",  "Finance",                  2018, "BlackRock",      "Portfolio Manager",            "Finance",           "New York, NY",       ["Python","R","Bloomberg","Risk Modeling"],        ["Investing","Startups","Golf"],         ["mentoring","referrals_career_advice"],                          "Managing equity portfolios at BlackRock.",                    False, "https://linkedin.com/in/davidkim"),
    ("Zara Ahmed",      "zara.ahmed@alumni.stonybrook.edu",   "ms",  "Biomedical Informatics",   2021, "NIH",            "Research Fellow",              "Healthcare",        "Bethesda, MD",       ["Python","R","Bioinformatics","SQL","FHIR"],      ["Genomics","Healthcare AI","Running"],   ["research_project_collab","mentoring","coffee_chat"],            "NIH fellow studying genomic basis of rare diseases.",         True,  None),
    ("Sam Rivera",      "sam.r@alumni.stonybrook.edu",        "bs",  "Computer Science",         2024, "Figma",          "Software Engineer",            "Tech",              "San Francisco, CA",  ["TypeScript","React","Rust","WebAssembly"],       ["Design Systems","Open Source","Music"], ["community_general_chat","coffee_chat","events_networking"],   "New grad at Figma building the editor core.",                 False, "https://linkedin.com/in/samrivera"),
    ("Laura Chen",      "laura.c@alumni.stonybrook.edu",      "phd", "Physics",                  2016, "IBM Research",   "Research Scientist",           "Research/Academia", "Yorktown Heights, NY",["Python","Qiskit","C++","LaTeX"],               ["Quantum Computing","Hiking","Chess"],   ["research_project_collab","mentoring"],                          "Quantum algorithms researcher at IBM.",                       False, "https://linkedin.com/in/laurachen"),
    ("Omar Hassan",     "omar.h@alumni.stonybrook.edu",       "ms",  "Computer Science",         2020, "Databricks",     "Staff Engineer",               "Tech",              "San Francisco, CA",  ["Spark","Python","Scala","Kafka","Delta Lake"],   ["Big Data","Distributed Systems","Soccer"], ["mentoring","referrals_career_advice","coffee_chat"],         "Staff engineer on Databricks lakehouse platform.",            True,  "https://linkedin.com/in/omarhassan"),

    # ── 30 more: diverse majors, industries, degrees, grad years ──────
    ("Grace Thompson",  "grace.t@alumni.stonybrook.edu",      "ba",  "Art History",              2013, "Sotheby's",      "Senior Specialist",            "Media",             "New York, NY",       ["Art Research","Writing","Appraisal"],            ["Fine Art","Museums","Travel"],          ["coffee_chat","events_networking","community_general_chat"],     "Appraising 20th-century art at Sotheby's auction house.",     False, None),
    ("Daniel Wu",       "daniel.wu@alumni.stonybrook.edu",    "bs",  "Biochemistry",             2017, "Regeneron",      "Scientist II",                 "Healthcare",        "Tarrytown, NY",      ["PCR","Cell Culture","Protein Purification","R"], ["Drug Discovery","Running","Cooking"],   ["mentoring","research_project_collab"],                          "Working on antibody therapeutics at Regeneron.",              False, "https://linkedin.com/in/danielwu"),
    ("Isabella Moreno", "isabella.m@alumni.stonybrook.edu",   "ba",  "Psychology",               2016, "NYC DOE",        "School Psychologist",          "Education",         "Brooklyn, NY",       ["Assessment","Counseling","CBT","Excel"],         ["Child Dev","Mindfulness","Reading"],    ["mentoring","coffee_chat","community_general_chat"],             "Supporting students with learning differences in NYC schools.",False, None),
    ("Thomas Nguyen",   "thomas.n@alumni.stonybrook.edu",     "bs",  "Civil Engineering",        2014, "AECOM",          "Project Engineer",             "Consulting",        "Philadelphia, PA",   ["AutoCAD","MATLAB","Revit","Project Mgmt"],       ["Infrastructure","Soccer","Photography"],["mentoring","events_networking"],                                "Designing bridges and transit infrastructure at AECOM.",      False, "https://linkedin.com/in/thomasnguyen"),
    ("Fatima Al-Rashid","fatima.ar@alumni.stonybrook.edu",    "phd", "Linguistics",              2018, "Cornell",        "Assistant Professor",          "Research/Academia", "Ithaca, NY",         ["Fieldwork","LaTeX","PRAAT","Python"],            ["Language Docs","Yoga","Baking"],        ["research_project_collab","mentoring"],                          "Documenting endangered Arabic dialects at Cornell.",          True,  None),
    ("Patrick Sullivan", "patrick.s@alumni.stonybrook.edu",   "mba", "Business Administration",  2012, "Johnson & Johnson","Senior Product Manager",     "Healthcare",        "New Brunswick, NJ",  ["Roadmapping","SQL","Agile","Market Research"],   ["Med Devices","Golf","History"],         ["mentoring","referrals_career_advice","coffee_chat"],            "PM for surgical robotics product line at J&J.",               False, "https://linkedin.com/in/patricksullivan"),
    ("Soo-Jin Park",    "soojin.p@alumni.stonybrook.edu",     "ms",  "Nutrition Science",        2020, "NewYork-Presbyterian","Registered Dietitian",   "Healthcare",        "New York, NY",       ["Medical Nutrition","Research","Excel","SPSS"],   ["Wellness","Cooking","K-dramas"],        ["coffee_chat","mentoring","community_general_chat"],             "Clinical dietitian specializing in oncology nutrition.",      True,  None),
    ("Andre Dubois",    "andre.d@alumni.stonybrook.edu",      "ma",  "Economics",                2011, "Federal Reserve","Economist",                   "Government",        "Washington, DC",     ["Stata","R","Econometrics","LaTeX"],              ["Macro Policy","Jazz","Running"],        ["mentoring","research_project_collab","coffee_chat"],            "Researching labor market dynamics at the NY Fed.",            True,  "https://linkedin.com/in/andredubois"),
    ("Chloe Martinez",  "chloe.m@alumni.stonybrook.edu",      "bs",  "Nursing",                  2019, "Mount Sinai",    "RN — ICU",                     "Healthcare",        "New York, NY",       ["Patient Care","Epic","Critical Care","ACLS"],    ["Travel Nursing","Hiking","Volunteering"],["coffee_chat","events_networking","community_general_chat"],   "ICU nurse at Mount Sinai with a passion for travel nursing.",  False, None),
    ("Benjamin Clark",  "ben.clark@alumni.stonybrook.edu",    "ba",  "History",                  2010, "NYC Law Dept",   "Deputy Corporation Counsel",   "Government",        "New York, NY",       ["Legal Research","Writing","Westlaw"],            ["History","Basketball","Craft Beer"],    ["mentoring","coffee_chat","referrals_career_advice"],            "Litigating constitutional cases for New York City.",          False, "https://linkedin.com/in/benjaminclark"),
    ("Amara Osei",      "amara.o@alumni.stonybrook.edu",      "ms",  "Environmental Science",    2021, "EPA",            "Environmental Scientist",      "Government",        "Washington, DC",     ["ArcGIS","Python","Environmental Modeling","R"],  ["Climate","Hiking","Photography"],       ["mentoring","research_project_collab","events_networking"],      "Modeling air quality impacts at the US EPA.",                 True,  "https://linkedin.com/in/amaraosei"),
    ("Ryan Fitzgerald",  "ryan.fitz@alumni.stonybrook.edu",   "bs",  "Journalism",               2018, "Newsday",        "Investigative Reporter",       "Media",             "Melville, NY",       ["Reporting","Editing","FOIA","Data Journalism"],  ["Long-form Journalism","Cycling","Dogs"],["coffee_chat","community_general_chat"],                         "Breaking local government accountability stories.",           False, None),
    ("Mei-Ling Ho",     "meiling.h@alumni.stonybrook.edu",    "phd", "Marine Science",           2019, "NOAA",           "Research Oceanographer",       "Research/Academia", "Silver Spring, MD",  ["MATLAB","Python","Oceanography","GIS"],          ["Climate Change","Scuba","Cooking"],     ["research_project_collab","mentoring","coffee_chat"],            "Studying coral reef resilience with NOAA.",                   True,  "https://linkedin.com/in/meilingho"),
    ("Carlos Reyes",    "carlos.r@alumni.stonybrook.edu",     "ba",  "Theater",                  2015, "Broadway Prod.", "Production Manager",           "Media",             "New York, NY",       ["Stage Mgmt","Budgeting","Crew Coordination"],    ["Theater","Travel","Music"],             ["events_networking","community_general_chat","coffee_chat"],     "Managing productions on and off Broadway.",                   False, None),
    ("Natasha Ivanova",  "natasha.i@alumni.stonybrook.edu",   "ms",  "Social Work",              2022, "Safe Horizon",   "Clinical Social Worker",       "Education",         "New York, NY",       ["Trauma-Informed Care","CBT","Case Mgmt"],        ["Mental Health","Yoga","Literature"],    ["mentoring","coffee_chat","community_general_chat"],             "Providing crisis counseling to domestic violence survivors.",  True,  None),
    ("William Okonkwo", "william.o@alumni.stonybrook.edu",    "mba", "Finance",                  2014, "JPMorgan Chase", "VP — Corporate Banking",       "Finance",           "New York, NY",       ["Financial Modeling","Excel","SQL","Bloomberg"],  ["Entrepreneurship","Soccer","Travel"],   ["mentoring","referrals_career_advice","coffee_chat"],            "Structuring leveraged finance deals at JPMorgan.",            True,  "https://linkedin.com/in/williamokonkwo"),
    ("Hannah Goldstein", "hannah.g@alumni.stonybrook.edu",    "ba",  "Sociology",                2020, "ACLU",           "Policy Advocate",              "Government",        "New York, NY",       ["Policy Research","Writing","Community Org"],     ["Civil Rights","Reading","Pottery"],     ["community_general_chat","coffee_chat","events_networking"],     "Advocating for criminal justice reform at the ACLU.",         False, "https://linkedin.com/in/hannahgoldstein"),
    ("Jae-Won Lim",     "jaewon.l@alumni.stonybrook.edu",     "bs",  "Physics",                  2023, "SpaceX",         "Propulsion Engineer",          "Tech",              "Hawthorne, CA",      ["MATLAB","Python","CFD","Thermodynamics"],        ["Space","Astrophysics","Guitar"],        ["mentoring","coffee_chat","research_project_collab"],            "Working on Raptor engine development at SpaceX.",             True,  "https://linkedin.com/in/jaewonlim"),
    ("Vanessa Pierre",  "vanessa.p@alumni.stonybrook.edu",    "ms",  "Public Health",            2018, "NYC Health Dept","Epidemiologist",               "Healthcare",        "New York, NY",       ["Epi Studies","SAS","R","Surveillance"],          ["Global Health","Salsa Dancing","Travel"],["mentoring","research_project_collab","events_networking"],    "Tracking infectious disease outbreaks across NYC.",           True,  "https://linkedin.com/in/vanessapierre"),
    ("Ethan Ross",      "ethan.r@alumni.stonybrook.edu",      "ba",  "Economics",                2009, "Bridgewater",    "Senior Investment Associate",  "Finance",           "Westport, CT",       ["Macro Research","Python","R","Bloomberg"],       ["Macro Investing","Squash","Podcasts"],  ["mentoring","coffee_chat","referrals_career_advice"],            "Researching global macro trends at Bridgewater Associates.",  False, "https://linkedin.com/in/ethanross"),
    ("Lena Fischer",    "lena.f@alumni.stonybrook.edu",       "phd", "Neuroscience",             2021, "Cold Spring Harbor Lab","Staff Scientist",       "Research/Academia", "Cold Spring Harbor, NY",["Patch Clamp","Python","MATLAB","Confocal"],    ["Neuroscience","Hiking","Photography"],  ["research_project_collab","mentoring"],                          "Studying synaptic plasticity mechanisms at CSHL.",            True,  "https://linkedin.com/in/lenafischer"),
    ("Marcus Webb",     "marcus.w@alumni.stonybrook.edu",     "bs",  "Accounting",               2016, "Deloitte",       "Senior Audit Manager",         "Finance",           "New York, NY",       ["GAAP","Excel","SAP","Tableau"],                  ["Personal Finance","Basketball","Travel"],["mentoring","referrals_career_advice","coffee_chat"],          "Leading audit engagements for Fortune 500 clients.",          False, "https://linkedin.com/in/marcuswebb"),
    ("Divya Menon",     "divya.m@alumni.stonybrook.edu",      "ms",  "Operations Research",      2020, "UPS",            "Supply Chain Analyst",         "Consulting",        "Atlanta, GA",        ["Python","OR Tools","SQL","Tableau","Excel"],     ["Optimization","Board Games","Cooking"],["mentoring","research_project_collab","coffee_chat"],            "Optimizing last-mile delivery networks at UPS.",              True,  "https://linkedin.com/in/divyamenon"),
    ("Sean Murphy",     "sean.m@alumni.stonybrook.edu",       "ba",  "Political Science",        2007, "US Senate",      "Legislative Director",         "Government",        "Washington, DC",     ["Policy Analysis","Writing","Advocacy","Comms"],  ["Foreign Policy","History","Golf"],      ["mentoring","coffee_chat","events_networking"],                  "Advising on healthcare and technology legislation.",          False, None),
    ("Tiffany Huang",   "tiffany.h@alumni.stonybrook.edu",    "ms",  "Architecture",             2019, "SHoP Architects","Project Architect",            "Media",             "New York, NY",       ["Rhino","Grasshopper","AutoCAD","Revit"],          ["Parametric Design","Photography","Travel"],["mentoring","coffee_chat","events_networking"],              "Designing mixed-use high-rises in NYC.",                      True,  "https://linkedin.com/in/tiffanyhuang"),
    ("Jerome Baptiste", "jerome.b@alumni.stonybrook.edu",     "mba", "Healthcare Management",    2017, "Memorial Sloan Kettering","Director of Operations","Healthcare",     "New York, NY",       ["Operations","Budget Mgmt","Lean","Excel"],       ["Healthcare Ops","Tennis","Volunteering"],["mentoring","referrals_career_advice","events_networking"],   "Running clinical operations at MSK Cancer Center.",           True,  "https://linkedin.com/in/jeromebaptiste"),
    ("Annika Svensson", "annika.s@alumni.stonybrook.edu",     "phd", "Mathematics",              2015, "Stony Brook University","Assistant Professor",    "Research/Academia", "Stony Brook, NY",    ["LaTeX","Python","Proof Techniques","Algebra"],   ["Topology","Running","Chess"],           ["research_project_collab","mentoring","coffee_chat"],            "Teaching pure math and researching geometric group theory.",  True,  "https://linkedin.com/in/annikasvensson"),
    ("DeShawn Harris",  "deshawn.h@alumni.stonybrook.edu",    "bs",  "Social Work",              2021, "Big Brothers Big Sisters","Program Coordinator","Education",        "Long Island, NY",    ["Case Mgmt","Community Outreach","Excel"],         ["Youth Mentorship","Basketball","Music"],["mentoring","community_general_chat","events_networking"],       "Connecting at-risk youth with mentors on Long Island.",       False, None),
    ("Penelope Cruz",   "penelope.c@alumni.stonybrook.edu",   "ma",  "Spanish Literature",       2014, "Random House",   "Senior Editor",                "Media",             "New York, NY",       ["Editing","Translation","Writing","Acquisitions"],["Latin Lit","Yoga","Film"],              ["coffee_chat","mentoring","community_general_chat"],             "Acquiring and editing Latin American fiction in translation.", False, "https://linkedin.com/in/penelopecruz"),
    ("Mohammed Al-Amin","mohammed.a@alumni.stonybrook.edu",   "ms",  "Electrical Engineering",   2016, "Siemens Energy",  "Systems Engineer",            "Tech",              "Orlando, FL",        ["SCADA","PLC","Python","Power Systems"],           ["Renewable Energy","Football","Chess"], ["mentoring","research_project_collab","coffee_chat"],            "Modernizing grid control systems at Siemens.",                True,  "https://linkedin.com/in/mohammedAlamin"),
    ("Olivia Bennett",  "olivia.b@alumni.stonybrook.edu",     "ba",  "Health Science",           2025, None,             None,                           None,                "Stony Brook, NY",    [],                                               ["Pre-Med","Volunteering","Hiking"],      ["community_general_chat","coffee_chat","mentoring"],             "Recent grad preparing for med school applications.",          False, None),
]


async def main():
    engine = create_async_engine(settings.database_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as db:
        created = 0
        for (name, email, degree, major, grad_year, company, title, industry,
             location, skills, interests, open_to, bio, is_intl, linkedin) in ALUMNI:

            # skip if already exists
            existing = await db.execute(select(AlumniUser).where(AlumniUser.email == email))
            if existing.scalar_one_or_none():
                print(f"  skip {email} (already exists)")
                continue

            user = AlumniUser(
                email=email,
                password_hash=hash_password("demo1234"),
                name=name,
                is_active=True,
                created_at=datetime.now(timezone.utc),
            )
            db.add(user)
            await db.flush()

            profile = AlumniProfile(
                user_id=user.id,
                major=major,
                degree=degree,
                graduation_year=grad_year,
                is_international=is_intl,
                current_company=company,
                job_title=title,
                industry=industry,
                location=location,
                skills=skills,
                interests=interests,
                open_to=open_to,
                linkedin_url=linkedin,
                bio=bio,
                is_visible=True,
                created_at=datetime.now(timezone.utc),
            )
            db.add(profile)
            created += 1
            print(f"  + {name} ({email})")

        await db.commit()
        print(f"\nDone — {created} alumni seeded.")

        # Generate embeddings for all profiles missing them
        print("\nGenerating embeddings for profiles without them...")
        provider = get_embedding_provider()
        all_profiles = (await db.execute(
            select(AlumniProfile, AlumniUser).join(AlumniUser, AlumniUser.id == AlumniProfile.user_id)
        )).all()

        embed_count = 0
        for profile, u in all_profiles:
            if profile.profile_embedding is not None:
                continue
            career_text = " ".join(filter(None, [
                u.name, profile.major, profile.degree,
                str(profile.graduation_year),
                profile.job_title, profile.current_company,
                profile.industry, profile.location, profile.bio,
            ]))
            skills_text = " ".join(profile.skills or [])
            interests_text = " ".join(profile.interests or [])
            vecs = await provider.embed([career_text, skills_text or "general", interests_text or "general"])
            profile.profile_embedding = vecs[0]
            profile.skills_embedding = vecs[1]
            profile.interests_embedding = vecs[2]
            embed_count += 1

        await db.commit()
        print(f"Embeddings generated for {embed_count} profiles.")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
