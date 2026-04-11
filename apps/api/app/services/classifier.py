"""
Hybrid intent classifier for Seawolf Ask alignment layer.

Architecture:
  1. Rule-based fast path  — obvious greetings, meaningless input, emergencies (~10ms)
  2. LLM classifier        — everything else, returns strict JSON

Intent labels (7):
  greeting                 social openers, thanks, farewells
  public_school_info       questions answerable from public SBU sources
  private_account_specific requires THIS user's personal account data
  ambiguous_public         SBU-related but too vague to answer without clarification
  human_support_needed     needs a real person or urgent escalation
  out_of_scope_non_sbu     not related to Stony Brook University at all
  no_meaningful_query      empty, filler, or deliberately empty input

Output schema:
  {
    "intent":                 "<one of 7 above>",
    "confidence":             0.0–1.0,
    "reasoning":              "<one sentence>",
    "clarification_question": "<only if ambiguous_public, else null>"
  }
"""

import re
import json
import logging
from app.services.ai_providers import get_llm_provider

logger = logging.getLogger(__name__)

# ─── Intent labels ────────────────────────────────────────────────────

INTENTS = {
    "greeting",
    "public_school_info",
    "private_account_specific",
    "ambiguous_public",
    "human_support_needed",
    "out_of_scope_non_sbu",
    "no_meaningful_query",
}

# ─── Rule-based fast paths (intentionally minimal) ───────────────────

FAST_GREETING = re.compile(
    r"^\s*(hi+|hello+|hey+|howdy|greetings|good (morning|afternoon|evening|day)|"
    r"thanks?|thank you|thx|ty|many thanks|appreciate (it|that|your help)|"
    r"that('s| was) (helpful|great|perfect|awesome|amazing|useful)|"
    r"bye+|goodbye|good ?night|see ya|take care|cya|later|"
    r"ok+|okay|got it|sounds good|great|awesome|perfect|nice|cool|"
    r"who are you\??|what can you do\??|what do you help with\??|"
    r"what('s| is) (your name|ask seawolves)\??|"
    r"can you help( me)?\??|are you (a bot|an ai|real)\??"
    r")\s*[!?.]*\s*$",
    re.IGNORECASE,
)

FAST_NO_MEANING = re.compile(
    r"^\s*(hmm+|hm+|uh+|um+|idk|i don'?t know|never mind|nevermind|nvm|"
    r"nothing|nothing for now|just (looking|browsing|checking)|"
    r"no (thanks?|question|questions?)|not? sure|forget it|"
    r"i don'?t have (a|any) questions?|no (worries|problem)|"
    r"\.+|\?+|…+)\s*$",
    re.IGNORECASE,
)

FAST_EMERGENCY = re.compile(
    r"\b(emergency|call 911|i feel unsafe|suicidal|want to (hurt|kill)|"
    r"in danger|need (an )?ambulance)\b",
    re.IGNORECASE,
)

# ─── Classifier system prompt ─────────────────────────────────────────

CLASSIFIER_SYSTEM = """You are an intent classifier for Seawolf Ask, the official chatbot for Stony Brook University (SBU).

Classify the user's message into EXACTLY ONE of these intents:

  greeting
      Social openers, thanks, farewells, "what can you do?" — no university question embedded.

  public_school_info
      Questions about publicly available SBU information: admissions, tuition, fees, deadlines,
      programs, housing options, dining plans, financial aid policies, library hours, parking,
      campus services, IT, academic calendar, clubs, faculty profiles, professor research interests,
      department contacts, course offerings, etc. The answer exists on a public SBU webpage.

  private_account_specific
      Requires THIS specific user's personal account data. Includes paraphrases like:
      "what's my grade", "did I pass", "what was my GPA last fall", "am I enrolled this term",
      "what's my account balance", "can you check my transcript", "did I get financial aid",
      "when does my refund post", "what classes am I taking", "check my enrollment",
      "what's my NetID status", "I can't log in to my account".
      IMPORTANT: classify as private even if phrased casually or indirectly.

  ambiguous_public
      Looks like a public info question but is too vague to answer accurately without knowing
      which specific aspect, term, or program the user means.
      Examples: "tell me about registration", "what are the fees?", "how do I apply?",
      "what's the deadline?", "tell me about housing".

  human_support_needed
      User needs to speak with a real person, is filing a complaint, in distress,
      or the topic clearly requires human intervention.

  out_of_scope_non_sbu
      The question has nothing to do with Stony Brook University or its services.
      Examples: weather, other universities, general knowledge, math problems,
      life advice, politics, sports, entertainment, cooking, coding help unrelated to SBU.

  no_meaningful_query
      Input is empty, a filler word, or the user has nothing to ask right now.
      Examples: "hmm", "idk", "never mind", "just looking", "nothing", "...".

RULES:
- "how much is my tuition as a freshman?" = public_school_info (asking about rates, not personal data)
- "what's my current tuition balance?" = private_account_specific (needs personal account data)
- "did I pass my exam?" = private_account_specific (requires personal grade data)
- "what was my GPA last fall?" = private_account_specific
- Only classify ambiguous_public if genuinely too vague — not just because it's short
- When in doubt between public_school_info and ambiguous_public, prefer public_school_info

Respond with ONLY valid JSON. No markdown, no explanation outside the JSON.

Output format:
{
  "intent": "<one of the seven intents above>",
  "confidence": <float 0.0–1.0>,
  "reasoning": "<one sentence explaining your classification>",
  "clarification_question": "<specific question IF intent is ambiguous_public, otherwise null>"
}"""

CLASSIFIER_FEW_SHOT = """Examples:

Q: "hi there!"
{"intent":"greeting","confidence":1.0,"reasoning":"Social opener with no university question.","clarification_question":null}

Q: "What is the tuition for out-of-state students?"
{"intent":"public_school_info","confidence":0.99,"reasoning":"Asking about publicly available tuition rates.","clarification_question":null}

Q: "when does my financial aid get deposited"
{"intent":"private_account_specific","confidence":0.97,"reasoning":"Asking about this specific user's personal financial aid disbursement date.","clarification_question":null}

Q: "what was my GPA last fall"
{"intent":"private_account_specific","confidence":0.98,"reasoning":"Requesting personal GPA data from a prior semester — requires account access.","clarification_question":null}

Q: "did I pass calc"
{"intent":"private_account_specific","confidence":0.97,"reasoning":"Asking whether this user passed a specific course — requires personal grade data.","clarification_question":null}

Q: "can you check my transcript"
{"intent":"private_account_specific","confidence":0.98,"reasoning":"Requesting access to personal transcript — private account data.","clarification_question":null}

Q: "am I enrolled this term"
{"intent":"private_account_specific","confidence":0.98,"reasoning":"Enrollment status is tied to the user's personal record.","clarification_question":null}

Q: "what's my account balance"
{"intent":"private_account_specific","confidence":0.97,"reasoning":"Account balance is personal financial data.","clarification_question":null}

Q: "tell me about registration"
{"intent":"ambiguous_public","confidence":0.85,"reasoning":"Too vague — could mean course registration, new student registration, or a specific term.","clarification_question":"Are you asking about course registration for a specific term (e.g., Fall 2026), or about registering as a new student?"}

Q: "what are the fees?"
{"intent":"ambiguous_public","confidence":0.88,"reasoning":"Unclear which fees — tuition, housing, dining, or other.","clarification_question":"Are you asking about tuition fees, housing fees, dining fees, or a different charge?"}

Q: "I need to speak to someone in the housing office"
{"intent":"human_support_needed","confidence":0.95,"reasoning":"User wants to talk to a person, not get an automated answer.","clarification_question":null}

Q: "what's the weather like today?"
{"intent":"out_of_scope_non_sbu","confidence":0.99,"reasoning":"Weather is not related to Stony Brook University services.","clarification_question":null}

Q: "what's 2 + 2?"
{"intent":"out_of_scope_non_sbu","confidence":0.99,"reasoning":"Math question unrelated to SBU.","clarification_question":null}

Q: "how do I get into Harvard?"
{"intent":"out_of_scope_non_sbu","confidence":0.97,"reasoning":"Question is about a different university, not SBU.","clarification_question":null}

Q: "hmm"
{"intent":"no_meaningful_query","confidence":1.0,"reasoning":"Filler word with no question.","clarification_question":null}

Q: "never mind"
{"intent":"no_meaningful_query","confidence":1.0,"reasoning":"User is withdrawing their query.","clarification_question":null}

Q: "just looking"
{"intent":"no_meaningful_query","confidence":1.0,"reasoning":"No specific question to answer.","clarification_question":null}

Q: "How much does a parking permit cost?"
{"intent":"public_school_info","confidence":0.96,"reasoning":"Asking about publicly listed parking permit pricing.","clarification_question":null}

Q: "how much is tuition if I'm a freshman from New York?"
{"intent":"public_school_info","confidence":0.94,"reasoning":"Asking about in-state tuition rates — publicly listed, not personal data.","clarification_question":null}

Q: "What clubs are available at SBU?"
{"intent":"public_school_info","confidence":0.97,"reasoning":"Asking about publicly available student organization information.","clarification_question":null}

Q: "Who is the chair of the Computer Science department?"
{"intent":"public_school_info","confidence":0.97,"reasoning":"Asking about a publicly listed faculty/department leadership role at SBU.","clarification_question":null}

Q: "What are Professor Leman Akoglu's research interests?"
{"intent":"public_school_info","confidence":0.96,"reasoning":"Asking about a faculty member's publicly listed research profile.","clarification_question":null}

Q: "Does SBU CS department have professors working on NLP?"
{"intent":"public_school_info","confidence":0.95,"reasoning":"Asking about research areas covered by SBU faculty — publicly available information.","clarification_question":null}

Q: "Who teaches graduate algorithms at SBU?"
{"intent":"public_school_info","confidence":0.93,"reasoning":"Asking about faculty teaching assignments — publicly available course/faculty information.","clarification_question":null}

Q: "What is the email for the math department?"
{"intent":"public_school_info","confidence":0.97,"reasoning":"Asking for a publicly listed department contact.","clarification_question":null}

Q: "How do I contact my advisor?"
{"intent":"ambiguous_public","confidence":0.85,"reasoning":"Unclear which advisor or department — needs clarification.","clarification_question":"Which department or program is your advisor in? (e.g., CS, Business, Graduate School)"}

Now classify the following query and respond with ONLY the JSON object:"""


# ─── ClassificationResult ─────────────────────────────────────────────

class ClassificationResult:
    def __init__(
        self,
        intent: str,
        confidence: float,
        reasoning: str,
        clarification_question: str | None = None,
        source: str = "llm",
    ):
        self.intent = intent
        self.confidence = confidence
        self.reasoning = reasoning
        self.clarification_question = clarification_question
        self.source = source  # "rule" or "llm"

    def __repr__(self):
        return (
            f"ClassificationResult(intent={self.intent!r}, "
            f"confidence={self.confidence:.2f}, source={self.source!r})"
        )


# ─── Classifier ───────────────────────────────────────────────────────

async def classify_query(query: str) -> ClassificationResult:
    """
    Hybrid classifier: rule fast-path → LLM.

    Fast paths (no LLM call):
      - Obvious greeting
      - Meaningless / empty input
      - Emergency keywords
    Everything else goes through the LLM classifier.
    """
    q_stripped = query.strip()

    # ── Fast path: no meaningful input ──────────────────────────────
    if not q_stripped or FAST_NO_MEANING.match(q_stripped):
        return ClassificationResult(
            intent="no_meaningful_query",
            confidence=1.0,
            reasoning="Matched fast-path no-meaning pattern.",
            source="rule",
        )

    # ── Fast path: greeting ──────────────────────────────────────────
    if FAST_GREETING.match(q_stripped):
        return ClassificationResult(
            intent="greeting",
            confidence=1.0,
            reasoning="Matched fast-path greeting pattern.",
            source="rule",
        )

    # ── Fast path: emergency ─────────────────────────────────────────
    if FAST_EMERGENCY.search(q_stripped):
        return ClassificationResult(
            intent="human_support_needed",
            confidence=1.0,
            reasoning="Matched fast-path emergency pattern.",
            source="rule",
        )

    # ── LLM classifier ───────────────────────────────────────────────
    return await _llm_classify(q_stripped)


async def _llm_classify(query: str) -> ClassificationResult:
    """Call the LLM with a structured classification prompt and parse JSON output."""
    llm = get_llm_provider()
    prompt = f"{CLASSIFIER_FEW_SHOT}\n\nQ: \"{query}\""

    try:
        raw = await llm.generate(
            prompt=prompt,
            system=CLASSIFIER_SYSTEM,
            max_tokens=200,
        )
        result = _parse_classification(raw)
        if result:
            return result
        logger.warning("LLM classifier returned unparseable output: %s", raw[:200])
    except Exception as e:
        logger.error("LLM classifier error: %s", e)

    return ClassificationResult(
        intent="public_school_info",
        confidence=0.4,
        reasoning="Classifier failed — defaulting to public_school_info.",
        source="fallback",
    )


def _parse_classification(raw: str) -> ClassificationResult | None:
    """Extract and validate JSON from LLM output."""
    raw = raw.strip()
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)

    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if not match:
        return None

    try:
        data = json.loads(match.group())
    except json.JSONDecodeError:
        return None

    intent = data.get("intent", "").strip()
    if intent not in INTENTS:
        return None

    confidence = float(data.get("confidence", 0.5))
    confidence = max(0.0, min(1.0, confidence))
    reasoning = str(data.get("reasoning", ""))[:300]

    clarification = data.get("clarification_question")
    if intent != "ambiguous_public":
        clarification = None
    elif not clarification:
        clarification = "Could you be more specific about what you're looking for?"

    return ClassificationResult(
        intent=intent,
        confidence=confidence,
        reasoning=reasoning,
        clarification_question=clarification,
        source="llm",
    )
