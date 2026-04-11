"""
Seed: 5 posts (different authors, varied topics), some comments & likes,
      + 10 random connections for wolfie@stonybrook.edu.
Run: docker compose exec api python seed_posts.py
"""
import asyncio, uuid, random
from datetime import datetime, timezone, timedelta

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

from app.core.config import get_settings
from app.models.models import AlumniUser, AlumniProfile, AlumniPost, AlumniComment, AlumniLike, AlumniConnection

settings = get_settings()


POSTS = [
    {
        "author_email": "alex.chen@alumni.stonybrook.edu",
        "content": (
            "Just hit my 3-year anniversary at Google Cloud ☁️\n\n"
            "When I graduated from SBU's CS program I had no idea what cloud infrastructure even meant. "
            "Looking back, the systems programming courses and the research I did with Prof. Bender were "
            "genuinely what got me through the interviews.\n\n"
            "If anyone's prepping for SWE roles at big tech — happy to do a mock interview or resume review. DM me!"
        ),
        "tags": ["#career", "#advice", "#jobs"],
        "days_ago": 2,
        "comments": [
            ("rahul.s@alumni.stonybrook.edu",   "Congrats Alex! Three years already? Time flies. Would love to connect sometime about distributed systems."),
            ("jordan.lee@alumni.stonybrook.edu", "This is super inspiring. Just started at Meta last month — the SBU CS curriculum really does prepare you well."),
            ("wolfie@stonybrook.edu",            "This is exactly what I needed to read today. Going to reach out about that mock interview!"),
        ],
        "likers": ["rahul.s@alumni.stonybrook.edu", "jordan.lee@alumni.stonybrook.edu",
                   "tyler.b@alumni.stonybrook.edu", "omar.h@alumni.stonybrook.edu",
                   "wolfie@stonybrook.edu"],
    },
    {
        "author_email": "sofia.rossi@alumni.stonybrook.edu",
        "content": (
            "Exciting news — our mRNA vaccine formulation paper just got accepted to Nature Biotechnology 🧬🎉\n\n"
            "Five years of bench work, two lab floods, and one global pandemic later… it's finally out. "
            "Huge thanks to my PhD advisor at SBU and the incredible team at Pfizer.\n\n"
            "The paper is open access. Drop a comment if you want the link!"
        ),
        "tags": ["#research", "#career"],
        "days_ago": 5,
        "comments": [
            ("zara.ahmed@alumni.stonybrook.edu", "Incredible work Sofia! Open access is the way to go. Please share the link!"),
            ("claire.d@alumni.stonybrook.edu",   "Nature Biotech is huge — congrats! Our paths may cross on the materials side of mRNA delivery 😄"),
            ("lena.f@alumni.stonybrook.edu",     "This is phenomenal. The SBU biology/biomed pipeline is seriously underrated."),
        ],
        "likers": ["zara.ahmed@alumni.stonybrook.edu", "claire.d@alumni.stonybrook.edu",
                   "daniel.wu@alumni.stonybrook.edu", "vanessa.p@alumni.stonybrook.edu",
                   "wolfie@stonybrook.edu", "priya.patel@alumni.stonybrook.edu"],
    },
    {
        "author_email": "marcus.j@alumni.stonybrook.edu",
        "content": (
            "Unpopular opinion: the best MBA skill isn't finance or strategy — it's learning how to run a meeting.\n\n"
            "Seriously. I've sat through hundreds of hours of meetings that could've been emails. "
            "The people who stand out early in their careers are the ones who can structure a discussion, "
            "keep it on track, and get to a decision.\n\n"
            "What's the most underrated skill you wish you'd developed earlier? Drop it below 👇"
        ),
        "tags": ["#advice", "#career", "#networking"],
        "days_ago": 8,
        "comments": [
            ("emma.w@alumni.stonybrook.edu",     "100% this. Also: writing clearly and concisely. Emails that actually get read are a superpower."),
            ("william.o@alumni.stonybrook.edu",  "Storytelling with data. Anyone can make a chart. Very few can make it mean something to a room of non-technical execs."),
            ("hannah.g@alumni.stonybrook.edu",   "Saying no gracefully. Especially early career when everyone wants to prove themselves."),
            ("marcus.w@alumni.stonybrook.edu",   "Active listening, no question. Most people are just waiting for their turn to talk."),
        ],
        "likers": ["emma.w@alumni.stonybrook.edu", "william.o@alumni.stonybrook.edu",
                   "ethan.r@alumni.stonybrook.edu", "patrick.s@alumni.stonybrook.edu",
                   "divya.m@alumni.stonybrook.edu", "wolfie@stonybrook.edu",
                   "sean.m@alumni.stonybrook.edu"],
    },
    {
        "author_email": "amara.o@alumni.stonybrook.edu",
        "content": (
            "SBU alumni in the DC/MD/VA area — let's build a stronger community here! 🌊\n\n"
            "I've been at the EPA for two years and I keep bumping into Seawolves at policy events, "
            "think tanks, and federal agencies. We should make this intentional.\n\n"
            "Thinking of organizing a casual meetup in the spring — happy hour in DC, no agenda, "
            "just good people. Who's interested? React or comment and I'll start a group chat 🙌"
        ),
        "tags": ["#events", "#networking", "#general"],
        "days_ago": 1,
        "comments": [
            ("sean.m@alumni.stonybrook.edu",     "Count me in! Always great to see more SBU folks on the Hill."),
            ("andre.d@alumni.stonybrook.edu",    "Definitely interested — the NY Fed has a DC presence and I'm down there fairly often."),
            ("jerome.b@alumni.stonybrook.edu",   "I travel to DC monthly for work — would love to join!"),
        ],
        "likers": ["sean.m@alumni.stonybrook.edu", "andre.d@alumni.stonybrook.edu",
                   "hannah.g@alumni.stonybrook.edu", "vanessa.p@alumni.stonybrook.edu"],
    },
    {
        "author_email": "aisha.k@alumni.stonybrook.edu",
        "content": (
            "Hot take: recommendation systems are a lot more about human psychology than machine learning.\n\n"
            "The hardest part of my job at Netflix isn't the model architecture — it's understanding "
            "why someone watches a documentary at 11pm on a Tuesday vs. a romcom on Friday night. "
            "Context, mood, and social cues matter more than we think.\n\n"
            "Shoutout to the HCI and cognitive science folks at SBU — your work is underappreciated "
            "in ML circles and genuinely makes products better 🧠\n\n"
            "What's a non-CS discipline you think belongs in ML teams? I'll start: anthropology."
        ),
        "tags": ["#research", "#career", "#general"],
        "days_ago": 3,
        "comments": [
            ("nina.v@alumni.stonybrook.edu",     "Philosophy of mind, 100%. The way we define 'understanding' in AI is deeply philosophical."),
            ("priya.patel@alumni.stonybrook.edu","Economics and behavioral economics especially. Loss aversion shapes so much of how people interact with products."),
            ("wolfie@stonybrook.edu",            "This is a great point. Taking an HCI elective changed how I think about building software."),
        ],
        "likers": ["nina.v@alumni.stonybrook.edu", "priya.patel@alumni.stonybrook.edu",
                   "laura.c@alumni.stonybrook.edu", "wolfie@stonybrook.edu",
                   "sam.r@alumni.stonybrook.edu", "tyler.b@alumni.stonybrook.edu",
                   "mei.lin@alumni.stonybrook.edu"],
    },
]

CONNECTION_COUNT = 10


async def main():
    engine = create_async_engine(settings.database_url, echo=False)
    Session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with Session() as db:
        # Build email → user lookup
        all_users_result = await db.execute(select(AlumniUser))
        all_users = {u.email: u for u in all_users_result.scalars().all()}

        all_profiles_result = await db.execute(select(AlumniProfile))
        all_profiles = {p.user_id: p for p in all_profiles_result.scalars().all()}

        wolfie = all_users.get("wolfie@stonybrook.edu")
        if not wolfie:
            print("wolfie@stonybrook.edu not found — skipping connections")

        # ── Seed posts ───────────────────────────────────────────────
        posts_created = 0
        for post_data in POSTS:
            author = all_users.get(post_data["author_email"])
            if not author:
                print(f"  skip post — author {post_data['author_email']} not found")
                continue

            author_profile = all_profiles.get(author.id)
            if not author_profile:
                print(f"  skip post — {post_data['author_email']} has no profile")
                continue

            created_at = datetime.now(timezone.utc) - timedelta(days=post_data["days_ago"])
            post = AlumniPost(
                author_id=author_profile.id,
                content=post_data["content"],
                tags=post_data["tags"],
                likes_count=len(post_data["likers"]),
                comments_count=len(post_data["comments"]),
                created_at=created_at,
            )
            db.add(post)
            await db.flush()

            # Comments
            for i, (commenter_email, text) in enumerate(post_data["comments"]):
                commenter = all_users.get(commenter_email)
                if not commenter:
                    continue
                commenter_profile = all_profiles.get(commenter.id)
                if not commenter_profile:
                    continue
                comment = AlumniComment(
                    post_id=post.id,
                    author_id=commenter_profile.id,
                    content=text,
                    created_at=created_at + timedelta(hours=i + 1),
                )
                db.add(comment)

            # Likes
            for liker_email in post_data["likers"]:
                liker = all_users.get(liker_email)
                if not liker:
                    continue
                db.add(AlumniLike(post_id=post.id, user_id=liker.id))

            posts_created += 1
            print(f"  + post by {author.name}: {post_data['content'][:60]}…")

        await db.commit()
        print(f"\n{posts_created} posts created.")

        # ── Seed connections for wolfie ───────────────────────────────
        if wolfie:
            # Get all users except wolfie
            others = [u for e, u in all_users.items() if e != "wolfie@stonybrook.edu"]
            sample = random.sample(others, min(CONNECTION_COUNT, len(others)))

            conn_created = 0
            for target in sample:
                existing = (await db.execute(
                    select(AlumniConnection).where(
                        AlumniConnection.requester_id == wolfie.id,
                        AlumniConnection.target_id == target.id,
                    )
                )).scalar_one_or_none()
                if existing:
                    continue
                db.add(AlumniConnection(
                    requester_id=wolfie.id,
                    target_id=target.id,
                    created_at=datetime.now(timezone.utc) - timedelta(days=random.randint(1, 30)),
                ))
                conn_created += 1
                print(f"  🤝 wolfie ↔ {target.name}")

            await db.commit()
            print(f"\n{conn_created} connections added for wolfie.")


if __name__ == "__main__":
    asyncio.run(main())
