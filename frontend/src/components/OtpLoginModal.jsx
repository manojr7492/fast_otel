import React, { useState, useRef, useEffect } from 'react';
import {
  X,
  Mail,
  Zap,
  CheckCircle2,
  AlertCircle,
  Copy,
  ArrowRight,
  ShieldCheck,
  RefreshCw,
  Sparkles
} from 'lucide-react';
import { useAuthStore } from '../store/useAuthStore';
import { useNotificationStore } from '../store/useNotificationStore';

export default function OtpLoginModal() {
  const { isOtpModalOpen, closeOtpModal, demoOtp, requestOtp, verifyOtp } = useAuthStore();
  const { addToast } = useNotificationStore();

  const [step, setStep] = useState('input'); // 'input' | 'otp' | 'success'
  const [identifier, setIdentifier] = useState('customer@antigravity.io');
  const [otpDigits, setOtpDigits] = useState(['', '', '', '', '', '']);
  const [errorMessage, setErrorMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [autoFilled, setAutoFilled] = useState(false);
  const [timer, setTimer] = useState(300); // 5 minutes

  const digitRefs = [
    useRef(null),
    useRef(null),
    useRef(null),
    useRef(null),
    useRef(null),
    useRef(null),
  ];

  // Timer countdown
  useEffect(() => {
    let interval = null;
    if (step === 'otp' && timer > 0) {
      interval = setInterval(() => setTimer((t) => t - 1), 1000);
    }
    return () => clearInterval(interval);
  }, [step, timer]);

  if (!isOtpModalOpen) return null;

  const formatTimer = () => {
    const m = Math.floor(timer / 60);
    const s = timer % 60;
    return `${m}:${s < 10 ? '0' : ''}${s}`;
  };

  const handleRequestOtp = async (e) => {
    e?.preventDefault();
    if (!identifier.trim()) {
      setErrorMessage('Please enter an email or username.');
      return;
    }

    setErrorMessage('');
    setIsLoading(true);

    try {
      const res = await requestOtp(identifier.trim());
      setIsLoading(false);
      setStep('otp');
      setTimer(300);
      setOtpDigits(['', '', '', '', '', '']);

      addToast(
        'Verification Code Generated',
        `Your 6-digit OTP is ${res.code}. Auto-fill ready!`,
        'info'
      );

      // Focus first input box
      setTimeout(() => {
        digitRefs[0].current?.focus();
      }, 100);
    } catch (err) {
      setIsLoading(false);
      setErrorMessage(err.message || 'Failed to generate OTP code.');
    }
  };

  // One-Click Auto-Fill Handler
  const handleAutoFill = () => {
    const code = demoOtp.code || '849201';
    const digits = code.split('').slice(0, 6);
    setOtpDigits(digits);
    setAutoFilled(true);
    setErrorMessage('');

    // Focus last input box
    digitRefs[5].current?.focus();

    addToast(
      'OTP Auto-Filled',
      `Populated code [ ${digits.join(' ')} ] into verification boxes.`,
      'success'
    );

    setTimeout(() => setAutoFilled(false), 1500);
  };

  const handleDigitChange = (index, value) => {
    // Only permit digits
    const cleaned = value.replace(/\D/g, '');
    const newDigits = [...otpDigits];

    if (cleaned.length > 1) {
      // User pasted multiple digits
      const pasted = cleaned.split('').slice(0, 6);
      for (let i = 0; i < 6; i++) {
        newDigits[i] = pasted[i] || '';
      }
      setOtpDigits(newDigits);
      const nextIdx = Math.min(5, pasted.length - 1);
      digitRefs[nextIdx].current?.focus();
      return;
    }

    newDigits[index] = cleaned;
    setOtpDigits(newDigits);

    // Auto-advance to next box if digit entered
    if (cleaned && index < 5) {
      digitRefs[index + 1].current?.focus();
    }
  };

  const handleKeyDown = (index, e) => {
    if (e.key === 'Backspace' && !otpDigits[index] && index > 0) {
      digitRefs[index - 1].current?.focus();
    }
  };

  const handleVerifyOtp = async (e) => {
    e?.preventDefault();
    const fullCode = otpDigits.join('');

    if (fullCode.length < 6) {
      setErrorMessage('Please enter all 6 digits of your verification code.');
      return;
    }

    setErrorMessage('');
    setIsLoading(true);

    try {
      await verifyOtp(identifier.trim(), fullCode);
      setIsLoading(false);
      setStep('success');

      addToast(
        'Session Established',
        'Signed in successfully with OpenTelemetry W3C trace correlation.',
        'success'
      );

      // Auto close after celebrating success
      setTimeout(() => {
        closeOtpModal();
        setStep('input');
      }, 1400);
    } catch (err) {
      setIsLoading(false);
      setErrorMessage(err.response?.data?.message || err.message || 'Invalid verification code.');
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-fade-in">
      <div
        className="relative w-full max-w-md rounded-3xl glass-dropdown border border-slate-700/80 shadow-2xl p-6 sm:p-8 overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Close Modal Button */}
        <button
          onClick={closeOtpModal}
          className="absolute top-4 right-4 p-2 rounded-xl bg-slate-800/80 hover:bg-slate-700 text-slate-400 hover:text-white transition-colors"
        >
          <X className="w-4 h-4" />
        </button>

        {/* ============================================================== */}
        {/* STEP 1: Enter Email / Username */}
        {/* ============================================================== */}
        {step === 'input' && (
          <div>
            <div className="w-12 h-12 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400 mb-4">
              <Zap className="w-6 h-6 text-indigo-400" />
            </div>

            <h2 className="text-xl font-bold text-white mb-1">
              Frictionless OTP Sign In
            </h2>
            <p className="text-xs text-slate-400 mb-6">
              Enter your email or username. A 6-digit verification code will be generated and shown directly on your screen.
            </p>

            {/* Quick Preset Accounts */}
            <div className="mb-4">
              <span className="text-[11px] text-slate-400 uppercase font-semibold tracking-wider block mb-2">
                Quick Demo Accounts:
              </span>
              <div className="flex flex-wrap gap-1.5">
                {[
                  'customer@antigravity.io',
                  'satya.nadella@microsoft.com',
                  'alex.creator@tech.dev',
                ].map((demoUser) => (
                  <button
                    key={demoUser}
                    type="button"
                    onClick={() => setIdentifier(demoUser)}
                    className="px-2.5 py-1 rounded-lg bg-slate-800/90 hover:bg-slate-700 border border-slate-700/60 text-[11px] text-slate-300 transition-colors"
                  >
                    {demoUser.split('@')[0]}
                  </button>
                ))}
              </div>
            </div>

            <form onSubmit={handleRequestOtp} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1.5">
                  Email or Username
                </label>
                <div className="relative">
                  <Mail className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                  <input
                    type="text"
                    required
                    value={identifier}
                    onChange={(e) => setIdentifier(e.target.value)}
                    placeholder="e.g. customer@antigravity.io"
                    className="w-full pl-10 pr-4 py-2.5 bg-slate-900 border border-slate-700 rounded-xl text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  />
                </div>
              </div>

              {errorMessage && (
                <div className="flex items-center gap-2 p-3 rounded-xl bg-rose-950/50 border border-rose-800/50 text-xs text-rose-300">
                  <AlertCircle className="w-4 h-4 flex-shrink-0" />
                  <span>{errorMessage}</span>
                </div>
              )}

              <button
                type="submit"
                disabled={isLoading}
                className="w-full py-3 rounded-xl bg-gradient-to-r from-indigo-600 to-indigo-500 hover:from-indigo-500 hover:to-indigo-400 text-white font-medium text-sm shadow-lg shadow-indigo-600/30 flex items-center justify-center gap-2 transition-all hover:scale-[1.01] active:scale-[0.99] disabled:opacity-50"
              >
                {isLoading ? (
                  <RefreshCw className="w-4 h-4 animate-spin" />
                ) : (
                  <>
                    <span>Generate On-Screen Code</span>
                    <ArrowRight className="w-4 h-4" />
                  </>
                )}
              </button>
            </form>
          </div>
        )}

        {/* ============================================================== */}
        {/* STEP 2: On-Screen Code Display & 6-Digit Auto-Fill */}
        {/* ============================================================== */}
        {step === 'otp' && (
          <div>
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs text-indigo-400 font-semibold uppercase tracking-wider">
                Step 2 of 2: Verify Code
              </span>
              <span className="text-xs font-mono text-slate-400">
                Expires in {formatTimer()}
              </span>
            </div>

            <h2 className="text-xl font-bold text-white mb-1">
              Verify OTP Code
            </h2>
            <p className="text-xs text-slate-400 mb-4 truncate">
              Verification dispatched for <span className="text-white font-medium">{identifier}</span>
            </p>

            {/* KEY REQUIREMENT: PROMINENT ON-SCREEN OTP ALERT BANNER */}
            <div className="relative overflow-hidden mb-6 rounded-2xl bg-gradient-to-br from-indigo-900/40 via-indigo-950/70 to-slate-900 border border-indigo-500/40 p-4 shadow-lg shadow-indigo-950/50">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <span className="flex h-2 w-2 rounded-full bg-emerald-400 animate-ping" />
                  <span className="text-[11px] font-bold uppercase tracking-wider text-emerald-400">
                    Live Demo Mode Active
                  </span>
                </div>
                <span className="text-[10px] text-slate-400 font-mono">
                  Notification: Delivered
                </span>
              </div>

              <div className="flex items-center justify-between gap-3 bg-black/40 p-3 rounded-xl border border-indigo-500/20">
                <div>
                  <span className="block text-[11px] text-slate-300">
                    Your verification code is:
                  </span>
                  <span className="text-2xl font-extrabold tracking-widest text-white font-mono text-indigo-200">
                    {demoOtp.code || '849201'}
                  </span>
                </div>

                {/* KEY REQUIREMENT: ONE-CLICK AUTO-FILL BUTTON */}
                <button
                  type="button"
                  onClick={handleAutoFill}
                  className={`flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-semibold shadow-md transition-all ${
                    autoFilled
                      ? 'bg-emerald-600 text-white scale-105'
                      : 'bg-indigo-600 hover:bg-indigo-500 text-white hover:scale-105 active:scale-95'
                  }`}
                >
                  <Sparkles className="w-3.5 h-3.5" />
                  <span>{autoFilled ? 'Auto-Filled!' : 'One-Click Auto-Fill'}</span>
                </button>
              </div>
            </div>

            {/* 6 Individual Digit Input Boxes */}
            <form onSubmit={handleVerifyOtp} className="space-y-5">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-2">
                  Enter 6-Digit Code
                </label>
                <div className="grid grid-cols-6 gap-2 sm:gap-3">
                  {otpDigits.map((digit, idx) => (
                    <input
                      key={idx}
                      ref={digitRefs[idx]}
                      type="text"
                      inputMode="numeric"
                      maxLength={1}
                      value={digit}
                      onChange={(e) => handleDigitChange(idx, e.target.value)}
                      onKeyDown={(e) => handleKeyDown(idx, e)}
                      className="w-full aspect-square text-center text-lg sm:text-xl font-bold font-mono bg-slate-900 border-2 border-slate-700/80 focus:border-indigo-500 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-indigo-500/30 transition-all"
                    />
                  ))}
                </div>
              </div>

              {errorMessage && (
                <div className="flex items-center gap-2 p-3 rounded-xl bg-rose-950/50 border border-rose-800/50 text-xs text-rose-300">
                  <AlertCircle className="w-4 h-4 flex-shrink-0" />
                  <span>{errorMessage}</span>
                </div>
              )}

              <button
                type="submit"
                disabled={isLoading || otpDigits.join('').length < 6}
                className="w-full py-3 rounded-xl bg-gradient-to-r from-emerald-600 to-emerald-500 hover:from-emerald-500 hover:to-emerald-400 text-white font-medium text-sm shadow-lg shadow-emerald-900/30 flex items-center justify-center gap-2 transition-all hover:scale-[1.01] active:scale-[0.99] disabled:opacity-40"
              >
                {isLoading ? (
                  <RefreshCw className="w-4 h-4 animate-spin" />
                ) : (
                  <>
                    <CheckCircle2 className="w-4 h-4" />
                    <span>Verify & Establish Session</span>
                  </>
                )}
              </button>

              <div className="flex items-center justify-between text-xs text-slate-400 pt-2 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setStep('input')}
                  className="hover:text-white transition-colors"
                >
                  Change identifier
                </button>
                <button
                  type="button"
                  onClick={handleRequestOtp}
                  className="text-indigo-400 hover:text-indigo-300 transition-colors flex items-center gap-1"
                >
                  <RefreshCw className="w-3 h-3" /> Resend OTP
                </button>
              </div>
            </form>
          </div>
        )}

        {/* ============================================================== */}
        {/* STEP 3: Verification Success Animation */}
        {/* ============================================================== */}
        {step === 'success' && (
          <div className="text-center py-8">
            <div className="w-16 h-16 rounded-full bg-emerald-500/20 border-2 border-emerald-500 flex items-center justify-center mx-auto text-emerald-400 mb-4 animate-bounce">
              <CheckCircle2 className="w-8 h-8" />
            </div>
            <h3 className="text-xl font-bold text-white mb-2">
              Welcome to ShopSphere!
            </h3>
            <p className="text-xs text-slate-300 max-w-xs mx-auto">
              Your customer session has been created. W3C trace context is now active for all your checkout transactions.
            </p>
          </div>
        )}

      </div>
    </div>
  );
}

