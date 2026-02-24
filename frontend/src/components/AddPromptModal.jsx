import { useState } from 'react';
import { addCustomPrompt } from '../api/promptApi';

export function AddPromptModal({ isOpen, onClose }) {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [promptBody, setPromptBody] = useState('');
  const [category, setCategory] = useState('');
  const [status, setStatus] = useState('idle'); // idle, submitting, success, error
  const [errorMessage, setErrorMessage] = useState('');

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setStatus('submitting');
    setErrorMessage('');

    const res = await addCustomPrompt({
      title,
      description,
      prompt_body: promptBody,
      category: category || 'custom'
    });

    if (res.type === 'success') {
      setStatus('success');
      setTimeout(() => {
        onClose();
        setTitle('');
        setDescription('');
        setPromptBody('');
        setCategory('');
        setStatus('idle');
      }, 2000);
    } else {
      setStatus('error');
      setErrorMessage(res.error || 'Failed to submit prompt');
    }
  };

  return (
    <div className="modal-overlay">
      <div className="modal-content">
        <div className="modal-header">
          <h2 className="modal-title">Submit a Custom Prompt</h2>
          <button className="modal-close" onClick={onClose} aria-label="Close modal">
            &times;
          </button>
        </div>

        {status === 'success' ? (
          <div className="modal-success-state">
            <div className="success-icon">✨</div>
            <p>Prompt submitted successfully!</p>
          </div>
        ) : (
          <form className="modal-form" onSubmit={handleSubmit}>
            <div className="form-group">
              <label htmlFor="prompt-title">Title <span className="required">*</span></label>
              <input
                id="prompt-title"
                type="text"
                placeholder="E.g., Python Code Generator"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                required
                disabled={status === 'submitting'}
              />
            </div>

            <div className="form-group">
              <label htmlFor="prompt-category">Category</label>
              <input
                id="prompt-category"
                type="text"
                placeholder="E.g., coding, creative, general"
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                disabled={status === 'submitting'}
              />
            </div>

            <div className="form-group">
              <label htmlFor="prompt-description">Description</label>
              <input
                id="prompt-description"
                type="text"
                placeholder="Brief explanation of what this prompt does"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                disabled={status === 'submitting'}
              />
            </div>

            <div className="form-group">
              <label htmlFor="prompt-body">Prompt Content <span className="required">*</span></label>
              <textarea
                id="prompt-body"
                placeholder="Enter the actual prompt here..."
                value={promptBody}
                onChange={(e) => setPromptBody(e.target.value)}
                required
                rows={6}
                disabled={status === 'submitting'}
              />
            </div>

            {status === 'error' && <div className="form-error">{errorMessage}</div>}

            <div className="modal-footer">
              <button
                type="button"
                className="action-button"
                onClick={onClose}
                disabled={status === 'submitting'}
              >
                Cancel
              </button>
              <button
                type="submit"
                className="cta-button"
                disabled={status === 'submitting' || !title.trim() || !promptBody.trim()}
              >
                {status === 'submitting' ? 'Submitting...' : 'Submit Prompt'}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
