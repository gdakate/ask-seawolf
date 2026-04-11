"use client";
import { useState, useRef } from "react";
import { useRouter } from "next/navigation";
import { createProfile, parseResume } from "@/lib/api";

const DEGREES = ["bs","ba","ms","ma","phd","mba","other"];
const DEGREE_LABELS: Record<string,string> = { bs:"B.S.",ba:"B.A.",ms:"M.S.",ma:"M.A.",phd:"Ph.D.",mba:"MBA",other:"Other" };

const OPEN_TO_OPTIONS = [
  { key: "coffee_chat",              label: "☕ Coffee Chat" },
  { key: "mentoring",                label: "🎓 Mentoring" },
  { key: "referrals_career_advice",  label: "💼 Referrals / Career Advice" },
  { key: "research_project_collab",  label: "🔬 Research / Project Collaboration" },
  { key: "community_general_chat",   label: "💬 Community / General Chat" },
  { key: "events_networking",        label: "🤝 Events / Networking" },
];

const INDUSTRIES = ["Tech","Finance","Healthcare","Research/Academia","Consulting","Government","Startup","Media","Education","Other"];

const CURRENT_YEAR = new Date().getFullYear();

type FormData = {
  major: string; degree: string; graduation_year: number; is_international: boolean;
  current_company: string; job_title: string; industry: string; location: string;
  skills: string[]; interests: string[]; open_to: string[];
  linkedin_url: string; bio: string;
};

const EMPTY: FormData = {
  major: "", degree: "bs", graduation_year: CURRENT_YEAR, is_international: false,
  current_company: "", job_title: "", industry: "", location: "",
  skills: [], interests: [], open_to: [],
  linkedin_url: "", bio: "",
};

function TagInput({ label, value, onChange, placeholder }: {
  label: string; value: string[]; onChange: (v: string[]) => void; placeholder: string;
}) {
  const [input, setInput] = useState("");
  const add = () => {
    const t = input.trim();
    if (t && !value.includes(t)) onChange([...value, t]);
    setInput("");
  };
  return (
    <div>
      <label className="block text-xs font-medium text-[var(--text-secondary)] mb-1.5">{label}</label>
      <div className="flex flex-wrap gap-1.5 mb-2">
        {value.map((t) => (
          <span key={t} className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-[var(--accent)]/10 text-[var(--accent)] text-xs font-medium">
            {t}
            <button onClick={() => onChange(value.filter((x) => x !== t))} className="hover:text-red-400 leading-none">×</button>
          </span>
        ))}
      </div>
      <div className="flex gap-2">
        <input value={input} onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => { if (e.key === "Enter") { e.preventDefault(); add(); } }}
          placeholder={placeholder}
          className="flex-1 px-3 py-2 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border)] text-sm text-[var(--text-primary)] outline-none focus:border-water-current/60" />
        <button type="button" onClick={add}
          className="px-3 py-2 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border)] text-sm text-[var(--text-muted)] hover:text-[var(--accent)]">
          Add
        </button>
      </div>
    </div>
  );
}

export default function OnboardingPage() {
  const router = useRouter();
  const [form, setForm] = useState<FormData>({ ...EMPTY });
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [parsing, setParsing] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  const set = (k: keyof FormData, v: any) => setForm((f) => ({ ...f, [k]: v }));

  const handleResume = async (file: File) => {
    setParsing(true);
    try {
      const { extracted } = await parseResume(file);
      setForm((f) => ({
        ...f,
        major: extracted.major || f.major,
        degree: extracted.degree || f.degree,
        graduation_year: extracted.graduation_year || f.graduation_year,
        current_company: extracted.current_company || f.current_company,
        job_title: extracted.job_title || f.job_title,
        industry: extracted.industry || f.industry,
        location: extracted.location || f.location,
        skills: extracted.skills?.length ? extracted.skills : f.skills,
        interests: extracted.interests?.length ? extracted.interests : f.interests,
        bio: extracted.bio || f.bio,
      }));
    } catch { /* silent fail — resume parse is optional */ }
    finally { setParsing(false); }
  };

  const handleSubmit = async () => {
    if (!form.major || !form.degree || !form.graduation_year) {
      setError("Major, degree and graduation year are required"); return;
    }
    setLoading(true); setError("");
    try {
      await createProfile({
        ...form,
        current_company: form.current_company || null,
        job_title: form.job_title || null,
        industry: form.industry || null,
        location: form.location || null,
        linkedin_url: form.linkedin_url || null,
        bio: form.bio || null,
      });
      router.push("/feed");
    } catch (err: any) {
      setError(err.message || "Failed to save profile");
    } finally { setLoading(false); }
  };

  return (
    <div className="max-w-2xl mx-auto px-4 py-10">
      {/* Steps indicator */}
      <div className="flex items-center gap-2 mb-8">
        {[1,2,3].map((s) => (
          <div key={s} className="flex items-center gap-2">
            <div className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold transition-colors ${
              s < step ? "bg-[var(--accent)] text-white" :
              s === step ? "bg-[var(--accent)]/20 text-[var(--accent)] border-2 border-[var(--accent)]" :
              "bg-[var(--bg-secondary)] text-[var(--text-muted)] border border-[var(--border)]"
            }`}>{s < step ? "✓" : s}</div>
            {s < 3 && <div className={`flex-1 h-0.5 w-8 ${s < step ? "bg-[var(--accent)]" : "bg-[var(--border)]"}`} />}
          </div>
        ))}
        <span className="ml-2 text-xs text-[var(--text-muted)]">
          {step === 1 ? "Academic" : step === 2 ? "Career" : "Interests"}
        </span>
      </div>

      <div className="glass-card rounded-2xl p-6 space-y-5">
        {error && (
          <div className="p-3 rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 text-sm text-red-700">
            {error}
          </div>
        )}

        {/* Step 1: Academic */}
        {step === 1 && (
          <>
            <div>
              <h2 className="font-display text-xl font-semibold text-[var(--text-primary)] mb-1">Academic Background</h2>
              <p className="text-sm text-[var(--text-muted)]">Tell us about your time at Stony Brook</p>
            </div>

            {/* Resume upload */}
            <div className="p-4 rounded-xl border-2 border-dashed border-[var(--border)] hover:border-water-current/40 transition-colors text-center cursor-pointer"
              onClick={() => fileRef.current?.click()}>
              <input ref={fileRef} type="file" accept=".pdf,.txt" className="hidden"
                onChange={(e) => e.target.files?.[0] && handleResume(e.target.files[0])} />
              {parsing ? (
                <div className="text-sm text-[var(--accent)]">Parsing resume...</div>
              ) : (
                <>
                  <div className="text-2xl mb-1">📄</div>
                  <p className="text-sm font-medium text-[var(--text-secondary)]">Upload Resume (optional)</p>
                  <p className="text-xs text-[var(--text-muted)]">PDF or TXT — auto-fills your profile</p>
                </>
              )}
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-medium text-[var(--text-secondary)] mb-1.5">Major *</label>
                <input value={form.major} onChange={(e) => set("major", e.target.value)}
                  placeholder="Computer Science" required
                  className="w-full px-3 py-2.5 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border)] text-sm text-[var(--text-primary)] outline-none focus:border-water-current/60" />
              </div>
              <div>
                <label className="block text-xs font-medium text-[var(--text-secondary)] mb-1.5">Degree *</label>
                <select value={form.degree} onChange={(e) => set("degree", e.target.value)}
                  className="w-full px-3 py-2.5 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border)] text-sm text-[var(--text-primary)] outline-none">
                  {DEGREES.map((d) => <option key={d} value={d}>{DEGREE_LABELS[d]}</option>)}
                </select>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-medium text-[var(--text-secondary)] mb-1.5">Graduation Year *</label>
                <input type="number" value={form.graduation_year}
                  onChange={(e) => set("graduation_year", parseInt(e.target.value) || CURRENT_YEAR)}
                  min={1957} max={CURRENT_YEAR + 6}
                  className="w-full px-3 py-2.5 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border)] text-sm text-[var(--text-primary)] outline-none" />
              </div>
              <div className="flex items-end pb-2">
                <label className="flex items-center gap-2 cursor-pointer select-none">
                  <input type="checkbox" checked={form.is_international}
                    onChange={(e) => set("is_international", e.target.checked)}
                    className="w-4 h-4 accent-[var(--accent)]" />
                  <span className="text-sm text-[var(--text-secondary)]">International student</span>
                </label>
              </div>
            </div>
          </>
        )}

        {/* Step 2: Career */}
        {step === 2 && (
          <>
            <div>
              <h2 className="font-display text-xl font-semibold text-[var(--text-primary)] mb-1">Career</h2>
              <p className="text-sm text-[var(--text-muted)]">Where are you now? (all optional)</p>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-medium text-[var(--text-secondary)] mb-1.5">Current Company</label>
                <input value={form.current_company} onChange={(e) => set("current_company", e.target.value)}
                  placeholder="Google"
                  className="w-full px-3 py-2.5 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border)] text-sm text-[var(--text-primary)] outline-none focus:border-water-current/60" />
              </div>
              <div>
                <label className="block text-xs font-medium text-[var(--text-secondary)] mb-1.5">Job Title</label>
                <input value={form.job_title} onChange={(e) => set("job_title", e.target.value)}
                  placeholder="Software Engineer"
                  className="w-full px-3 py-2.5 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border)] text-sm text-[var(--text-primary)] outline-none focus:border-water-current/60" />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-medium text-[var(--text-secondary)] mb-1.5">Industry</label>
                <select value={form.industry} onChange={(e) => set("industry", e.target.value)}
                  className="w-full px-3 py-2.5 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border)] text-sm text-[var(--text-primary)] outline-none">
                  <option value="">Select industry</option>
                  {INDUSTRIES.map((i) => <option key={i} value={i}>{i}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-xs font-medium text-[var(--text-secondary)] mb-1.5">Location</label>
                <input value={form.location} onChange={(e) => set("location", e.target.value)}
                  placeholder="New York, NY"
                  className="w-full px-3 py-2.5 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border)] text-sm text-[var(--text-primary)] outline-none focus:border-water-current/60" />
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-[var(--text-secondary)] mb-1.5">LinkedIn URL</label>
              <input value={form.linkedin_url} onChange={(e) => set("linkedin_url", e.target.value)}
                placeholder="https://linkedin.com/in/yourname"
                className="w-full px-3 py-2.5 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border)] text-sm text-[var(--text-primary)] outline-none focus:border-water-current/60" />
            </div>

            <div>
              <label className="block text-xs font-medium text-[var(--text-secondary)] mb-1.5">Bio</label>
              <textarea value={form.bio} onChange={(e) => set("bio", e.target.value)}
                placeholder="One or two sentences about yourself..."
                rows={3}
                className="w-full px-3 py-2.5 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border)] text-sm text-[var(--text-primary)] outline-none focus:border-water-current/60 resize-none" />
            </div>
          </>
        )}

        {/* Step 3: Skills, Interests, Open to */}
        {step === 3 && (
          <>
            <div>
              <h2 className="font-display text-xl font-semibold text-[var(--text-primary)] mb-1">Skills & Interests</h2>
              <p className="text-sm text-[var(--text-muted)]">These power the AI matching</p>
            </div>

            <TagInput label="Skills" value={form.skills} onChange={(v) => set("skills", v)}
              placeholder="Python, React, ML… (Enter to add)" />

            <TagInput label="Interests" value={form.interests} onChange={(v) => set("interests", v)}
              placeholder="AI, Startups, Biotech… (Enter to add)" />

            <div>
              <label className="block text-xs font-medium text-[var(--text-secondary)] mb-2">Open To (select all that apply)</label>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {OPEN_TO_OPTIONS.map(({ key, label }) => (
                  <button key={key} type="button"
                    onClick={() => set("open_to", form.open_to.includes(key)
                      ? form.open_to.filter((x) => x !== key)
                      : [...form.open_to, key])}
                    className={`px-3 py-2.5 rounded-lg border text-sm text-left transition-all ${
                      form.open_to.includes(key)
                        ? "border-[var(--accent)] bg-[var(--accent)]/10 text-[var(--accent)] font-medium"
                        : "border-[var(--border)] text-[var(--text-secondary)] hover:border-water-current/40"
                    }`}>
                    {label}
                  </button>
                ))}
              </div>
            </div>
          </>
        )}

        {/* Navigation */}
        <div className="flex justify-between pt-2">
          {step > 1 ? (
            <button onClick={() => setStep(step - 1)}
              className="px-4 py-2 rounded-lg border border-[var(--border)] text-sm text-[var(--text-muted)] hover:text-[var(--text-primary)] transition-colors">
              ← Back
            </button>
          ) : <div />}

          {step < 3 ? (
            <button onClick={() => { if (step === 1 && !form.major) { setError("Major is required"); return; } setError(""); setStep(step + 1); }}
              className="px-6 py-2 btn-water text-white rounded-lg text-sm font-semibold">
              Continue →
            </button>
          ) : (
            <button onClick={handleSubmit} disabled={loading}
              className="px-6 py-2 btn-water text-white rounded-lg text-sm font-semibold disabled:opacity-50">
              {loading ? "Saving..." : "Complete Profile →"}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
