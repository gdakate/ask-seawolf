export function Footer() {
  return (
    <footer className="border-t border-[var(--border)] bg-[var(--bg-secondary)]">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-8">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 text-sm">
          <div>
            <h3 className="font-display font-semibold text-[var(--text-primary)] mb-3">
              Seawolf Ask
            </h3>
            <p className="text-[var(--text-muted)] leading-relaxed">
              Answers are generated from official Stony Brook University sources.
              Always verify important details with the relevant office.
            </p>
          </div>
          <div>
            <h4 className="font-semibold text-[var(--text-primary)] mb-3">Quick Links</h4>
            <ul className="space-y-2 text-[var(--text-muted)]">
              <li>
                <a href="https://www.stonybrook.edu" className="hover:text-sbu-red transition-colors" target="_blank" rel="noopener noreferrer">
                  Stony Brook University
                </a>
              </li>
              <li>
                <a href="https://solar.stonybrook.edu" className="hover:text-sbu-red transition-colors" target="_blank" rel="noopener noreferrer">
                  SOLAR
                </a>
              </li>
              <li>
                <a href="https://www.stonybrook.edu/admissions/" className="hover:text-sbu-red transition-colors" target="_blank" rel="noopener noreferrer">
                  Admissions
                </a>
              </li>
            </ul>
          </div>
          <div>
            <h4 className="font-semibold text-[var(--text-primary)] mb-3">Disclaimer</h4>
            <p className="text-[var(--text-muted)] leading-relaxed text-xs">
              This AI assistant provides information based on publicly available
              Stony Brook University content. Responses may not reflect the most
              recent updates. For official guidance, contact the relevant
              university office directly.
            </p>
          </div>
        </div>
        <div className="mt-8 pt-6 border-t border-[var(--border)] text-center text-xs text-[var(--text-muted)]">
          &copy; {new Date().getFullYear()} Seawolf Ask
        </div>
      </div>
    </footer>
  );
}
