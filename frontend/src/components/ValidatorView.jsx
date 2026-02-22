import { useCallback, useState } from 'react';
import { VALIDATION_INSTRUCTION } from '../constants/validationInstruction';

export function ValidatorView() {
  const [customPrompt, setCustomPrompt] = useState('');

  const handleValidate = useCallback(() => {
    if (!customPrompt.trim()) return;

    // Combine validation instruction + the user's custom prompt verbatim
    const fullPayload = VALIDATION_INSTRUCTION + customPrompt;
    
    // Encode for URL
    const encoded = encodeURIComponent(fullPayload);
    
    // Open Claude with pre-filled prompt
    const claudeUrl = `https://claude.ai/new?q=${encoded}`;
    window.open(claudeUrl, '_blank', 'noopener,noreferrer');
  }, [customPrompt]);

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
      handleValidate();
    }
  };

  return (
    <div className="validator-view animate-fade-in fade-in-up delay-1">
      <div className="validator-header">
        <h2 className="validator-title">🧪 Custom Prompt Validator</h2>
        <p className="validator-description">
          Paste your own prompt below to have Claude grade it, break down its anatomy, 
          and teach you how to improve it using the Prompt Coach methodology.
        </p>
      </div>

      <div className="validator-input-container">
        <textarea
          className="validator-textarea"
          value={customPrompt}
          onChange={(e) => setCustomPrompt(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Paste your prompt here... (e.g., 'You are a senior software engineer. Please review the following code...')"
          aria-label="Custom Prompt Input"
          spellCheck="false"
        />
        <div className="validator-hint">
          Pro-tip: Press <kbd>Ctrl</kbd> + <kbd>Enter</kbd> to validate
        </div>
      </div>

      <div className="validator-actions">
        <button
          className="cta-button"
          onClick={handleValidate}
          disabled={!customPrompt.trim()}
        >
          <span className="cta-button-text">Validate on Claude</span>
          <span className="cta-button-icon">🔍</span>
        </button>
      </div>
    </div>
  );
}
