import { useCallback, useEffect, useRef, useState } from 'react';
import { usePrompt } from './hooks/usePrompt';

/* ─── Header ─── */
function Header({ theme, onToggleTheme }) {
  return (
    <header className="header">
      <div className="header-logo">
        <span className="header-logo-icon">⚡</span>
        <span className="header-logo-text">Daily Prompt</span>
      </div>
      <button
        className="theme-toggle"
        onClick={onToggleTheme}
        aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
        title={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
      >
        <span className="theme-toggle-icon">{theme === 'dark' ? '☀️' : '🌙'}</span>
      </button>
    </header>
  );
}

/* ─── Hero Section ─── */
function HeroSection({ stats, status, onRequestPrompt, onNextPrompt }) {
  const isIdle = status === 'idle';
  const isLoading = status === 'loading';
  const isRevealed = status === 'revealed';

  return (
    <section className="hero">
      <div className="hero-badge">
        <span className="hero-badge-dot"></span>
        Your Daily AI Prompt
      </div>

      <h1 className="hero-title">
        Discover a <span className="hero-title-gradient">New Prompt</span>
      </h1>

      <p className="hero-subtitle">
        A curated prompt from Anthropic's library, delivered one at a time. Never repeated.
      </p>

      <button
        className={`cta-button ${isIdle ? 'cta-button--idle' : ''} ${isRevealed ? 'cta-button--delivered' : ''}`}
        onClick={isRevealed ? onNextPrompt : onRequestPrompt}
        disabled={isLoading}
      >
        <span className="cta-button-icon">
          {isLoading ? '⏳' : isRevealed ? '⚡' : '⚡'}
        </span>
        {isLoading ? 'Finding your prompt...' : isRevealed ? 'Next Prompt' : "Get Today's Prompt"}
      </button>

      {stats && (
        <p className="counter">
          <span className="counter-number">{stats.served}</span> of{' '}
          <span className="counter-number">{stats.total}</span> prompts served
        </p>
      )}
    </section>
  );
}

/* ─── Typewriter Effect ─── */
function TypewriterText({ text, speed = 20 }) {
  const [displayed, setDisplayed] = useState('');
  const [done, setDone] = useState(false);
  const indexRef = useRef(0);

  useEffect(() => {
    setDisplayed('');
    setDone(false);
    indexRef.current = 0;

    if (!text) return;

    const interval = setInterval(() => {
      indexRef.current += 1;
      if (indexRef.current >= text.length) {
        setDisplayed(text);
        setDone(true);
        clearInterval(interval);
      } else {
        setDisplayed(text.slice(0, indexRef.current));
      }
    }, speed);

    return () => clearInterval(interval);
  }, [text, speed]);

  return (
    <span>
      {displayed}
      {!done && <span className="typewriter-cursor" />}
    </span>
  );
}

/* ─── Prompt Card ─── */
function PromptCard({ prompt }) {
  const [copied, setCopied] = useState(false);

  // Build combined text for copy
  const fullPromptText = [
    prompt.system_prompt ? `[System Instructions]\n${prompt.system_prompt}` : '',
    prompt.prompt_body ? `[User Prompt]\n${prompt.prompt_body}` : '',
  ].filter(Boolean).join('\n\n');

  const handleCopy = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(fullPromptText);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      const ta = document.createElement('textarea');
      ta.value = fullPromptText;
      document.body.appendChild(ta);
      ta.select();
      document.execCommand('copy');
      document.body.removeChild(ta);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  }, [fullPromptText]);

  const handleTryOnClaude = useCallback(() => {
    // Build the prompt to send to Claude
    let queryText = '';
    if (prompt.system_prompt && prompt.prompt_body) {
      queryText = `${prompt.system_prompt}\n\n${prompt.prompt_body}`;
    } else {
      queryText = prompt.system_prompt || prompt.prompt_body;
    }
    const encodedPrompt = encodeURIComponent(queryText);
    window.open(`https://claude.ai/new?q=${encodedPrompt}`, '_blank', 'noopener,noreferrer');
  }, [prompt.system_prompt, prompt.prompt_body]);

  return (
    <div className="prompt-card" role="article">
      <div className="prompt-card-header">
        <span className="prompt-card-number">
          Prompt #{prompt.serve_order}
        </span>
      </div>

      <h2 className="prompt-card-title">{prompt.title}</h2>

      {prompt.description && (
        <p className="prompt-card-description">{prompt.description}</p>
      )}

      {/* System Prompt Section */}
      {prompt.system_prompt && (
        <div className="prompt-section">
          <div className="prompt-section-label">
            <span className="prompt-section-icon">🧠</span> System Prompt
          </div>
          <div className="prompt-card-body prompt-card-body--system">
            <TypewriterText text={prompt.system_prompt} speed={12} />
          </div>
        </div>
      )}

      {/* User Prompt Section */}
      {prompt.prompt_body && (
        <div className="prompt-section">
          <div className="prompt-section-label">
            <span className="prompt-section-icon">💬</span> User Prompt
          </div>
          <div className="prompt-card-body">
            <TypewriterText text={prompt.prompt_body} speed={12} />
          </div>
        </div>
      )}

      <div className="prompt-card-footer">
        <span className="prompt-card-category">{prompt.category}</span>

        <div className="prompt-card-actions">
          <button
            className="action-button action-button--claude"
            onClick={handleTryOnClaude}
            title="Try this prompt on Claude"
          >
            🚀 Try on Claude
          </button>
          <a
            href={prompt.source_url}
            target="_blank"
            rel="noopener noreferrer"
            className="action-button"
          >
            🔗 Source
          </a>
          <button
            className={`action-button ${copied ? 'action-button--copied' : ''}`}
            onClick={handleCopy}
          >
            {copied ? '✓ Copied' : '📋 Copy'}
          </button>
        </div>
      </div>
    </div>
  );
}

/* ─── Loading State ─── */
function LoadingState() {
  return (
    <div className="skeleton-card" role="status" aria-label="Loading prompt">
      <div className="skeleton-line skeleton-line--title"></div>
      <div className="skeleton-line skeleton-line--desc"></div>
      <div className="skeleton-line skeleton-line--desc" style={{ width: '70%' }}></div>
      <div className="skeleton-line skeleton-line--body"></div>
      <div className="skeleton-line skeleton-line--tag"></div>
    </div>
  );
}

/* ─── Error State ─── */
function ErrorState({ error, onRetry }) {
  return (
    <div className="error-card" role="alert">
      <div className="error-icon">⚠️</div>
      <h2 className="error-title">Something went wrong</h2>
      <p className="error-message">{error || 'Failed to fetch your prompt. Please try again.'}</p>
      <button className="retry-button" onClick={onRetry}>
        🔄 Try Again
      </button>
    </div>
  );
}

/* ─── Exhausted State ─── */
function ExhaustedState({ stats }) {
  return (
    <div className="exhausted-card">
      <div className="particles">
        {Array.from({ length: 8 }, (_, i) => (
          <div key={i} className="particle" />
        ))}
      </div>
      <div className="exhausted-icon">✨</div>
      <h2 className="exhausted-title">All Prompts Discovered</h2>
      <p className="exhausted-message">
        You've explored every prompt in Anthropic's library. Check back as new ones are added.
      </p>
      {stats && (
        <p className="exhausted-counter">
          <span className="exhausted-counter-number">{stats.total}</span> of{' '}
          <span className="exhausted-counter-number">{stats.total}</span> prompts served
          — 100% explored
        </p>
      )}
    </div>
  );
}

/* ─── Footer ─── */
function Footer() {
  return (
    <footer className="footer">
      Built with prompts from{' '}
      <a
        href="https://docs.anthropic.com/en/prompt-library/library"
        target="_blank"
        rel="noopener noreferrer"
      >
        Anthropic
      </a>{' '}
      · Daily Prompt v1.0
    </footer>
  );
}

/* ═══ APP ═══ */
export default function App() {
  const { status, prompt, stats, error, requestPrompt, reset } = usePrompt();

  // Theme management
  const [theme, setTheme] = useState(() => {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('dailyprompt-theme') || 'dark';
    }
    return 'dark';
  });

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('dailyprompt-theme', theme);
  }, [theme]);

  const toggleTheme = useCallback(() => {
    setTheme(prev => prev === 'dark' ? 'light' : 'dark');
  }, []);

  const handleRetry = useCallback(() => {
    reset();
    requestPrompt();
  }, [reset, requestPrompt]);

  return (
    <div className="app">
      <Header theme={theme} onToggleTheme={toggleTheme} />

      <main className="main-content">
        {status !== 'exhausted' && (
          <HeroSection
            stats={stats}
            status={status}
            onRequestPrompt={requestPrompt}
            onNextPrompt={handleRetry}
          />
        )}

        {status === 'loading' && <LoadingState />}
        {status === 'revealed' && prompt && <PromptCard prompt={prompt} />}
        {status === 'error' && <ErrorState error={error} onRetry={handleRetry} />}
        {status === 'exhausted' && <ExhaustedState stats={stats} />}
      </main>

      <Footer />
    </div>
  );
}
