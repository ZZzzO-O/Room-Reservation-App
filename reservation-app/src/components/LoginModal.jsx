// file: src/components/LoginModal.jsx
// purpose: Modal for user authentication and quick demo profile selection
// author: Zin Zin Zaw Win
// date: 2026-10-20

import React, { useState } from 'react';

import { loginUser } from '../api/authApi';
import ModalShell from './ModalShell';
import { LABEL, INPUT, BTN_PRIMARY, BTN_SECONDARY, ERROR_BOX } from '../utils/styles';

const DEMO_PASSWORD = import.meta.env.DEV ? 'Test@1234' : '';
const DEMO_ACCOUNTS = import.meta.env.DEV ? [
  { id: 'demo-login-staff', label: 'Staff 1', email: 'staff1@cmkl.ac.th' },
  { id: 'demo-login-prof', label: 'Professor 1', email: 'prof1@cmkl.ac.th' },
] : [];

/**
 * Authentication modal dialog for signing into the application.
 * @param {Object} props
 * @param {boolean} props.isOpen - Whether modal is visible.
 * @param {function} props.onClose - Dismiss callback.
 * @param {function} props.onLoginSuccess - Callback invoked with authenticated user profile.
 * @returns {JSX.Element|null} The modal component.
 */
export default function LoginModal({ isOpen, onClose, onLoginSuccess }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrorMessage('');
    setIsLoading(true);

    try {
      const result = await loginUser(email, password);
      onLoginSuccess(result.user);
      onClose();
    } catch (err) {
      setErrorMessage(err.message || 'Authentication failed.');
    } finally {
      setIsLoading(false);
    }
  };

  const fillDemoAccount = (demoEmail) => {
    setEmail(demoEmail);
    setPassword(DEMO_PASSWORD);
    setErrorMessage('');
  };

  return (
    <ModalShell title="Sign in" onClose={onClose}>
      <form onSubmit={handleSubmit} className="p-5 space-y-4">
        {errorMessage && <div className={ERROR_BOX}>{errorMessage}</div>}

        <div>
          <label htmlFor="login-email" className={LABEL}>
            CMKL email
          </label>
          <input
            id="login-email"
            type="email"
            required
            autoComplete="username"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="name@cmkl.ac.th"
            className={INPUT}
          />
        </div>

        <div>
          <label htmlFor="login-password" className={LABEL}>
            Password
          </label>
          <input
            id="login-password"
            type="password"
            required
            autoComplete="current-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className={INPUT}
          />
        </div>

        {DEMO_ACCOUNTS.length > 0 && (
          <p className="text-xs text-slate-500 dark:text-slate-400">
            Test accounts:{' '}
            {DEMO_ACCOUNTS.map((account, idx) => (
            <React.Fragment key={account.id}>
              {idx > 0 && ' · '}
              <button
                type="button"
                id={account.id}
                onClick={() => fillDemoAccount(account.email)}
                className="font-medium text-brand-700 dark:text-brand-300 underline underline-offset-2 hover:text-brand-900 dark:hover:text-brand-200"
              >
                {account.label}
              </button>
            </React.Fragment>
            ))}
          </p>
        )}

        <div className="pt-1 flex justify-end gap-2">
          <button
            id="close-login-modal"
            type="button"
            onClick={onClose}
            className={BTN_SECONDARY}
          >
            Cancel
          </button>
          <button
            id="submit-login"
            type="submit"
            disabled={isLoading}
            className={BTN_PRIMARY}
          >
            {isLoading ? 'Signing in…' : 'Sign in'}
          </button>
        </div>
      </form>
    </ModalShell>
  );
}
