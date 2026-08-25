import React, { useState } from 'react';
import { ShieldCheck, Key, ArrowRight, Lock, AlertCircle, Eye, EyeOff, Shield } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { api, APIError } from '../../services/api';
import { motion } from 'framer-motion';

export const LoginView: React.FC = () => {
  const { setApiKey } = useAuth();
  const [inputKey, setInputKey] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    const cleanKey = inputKey.trim();
    if (!cleanKey) {
      setError('Please enter your API Key.');
      return;
    }

    setLoading(true);
    setError('');

    try {
      // Validate key against live authenticated endpoint
      await api.getDashboardSummary(cleanKey);
      // Backend returned HTTP 200 -> Authenticated successfully
      setApiKey(cleanKey);
    } catch (err: any) {
      if (err instanceof APIError) {
        if (err.statusCode === 401) {
          setError('Invalid API credential.');
        } else if (err.statusCode === 503 || err.statusCode === 502) {
          setError('SecureOps gateway is unavailable. Verify that the backend server is running.');
        } else {
          setError(err.message || 'Authentication failed. Please check your credentials.');
        }
      } else {
        setError('SecureOps gateway is unavailable. Verify that the backend server is running.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#090d16] flex items-center justify-center p-4 relative overflow-hidden select-none">
      {/* Subtle Background Lighting */}
      <div className="absolute -top-40 -left-40 w-96 h-96 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute -bottom-40 -right-40 w-96 h-96 bg-emerald-500/10 rounded-full blur-3xl pointer-events-none" />

      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.4 }}
        className="w-full max-w-md bg-[#111827]/90 border border-slate-800 rounded-2xl p-8 backdrop-blur-xl shadow-2xl relative z-10"
      >
        <div className="flex flex-col items-center text-center mb-8">
          <div className="w-14 h-14 rounded-2xl bg-gradient-to-tr from-cyan-600 to-emerald-500 flex items-center justify-center shadow-glow-cyan mb-4">
            <ShieldCheck className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-2xl font-bold text-white tracking-tight">SecureOps Gateway</h1>
          <p className="text-xs text-slate-400 mt-1 font-mono">Enterprise AI Security Operations Center</p>
        </div>

        {error && (
          <div className="mb-6 p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-400 text-xs flex items-center gap-2.5">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span className="font-mono text-[11px]">{error}</span>
          </div>
        )}

        <form onSubmit={handleLogin} className="space-y-5">
          <div>
            <label className="block text-xs font-mono text-slate-400 mb-2 font-medium">
              API Authorization Key
            </label>
            <div className="relative">
              <Key className="w-4 h-4 text-slate-500 absolute left-3.5 top-3.5" />
              <input
                type={showPassword ? 'text' : 'password'}
                value={inputKey}
                onChange={(e) => setInputKey(e.target.value)}
                placeholder="Enter API Authorization Key"
                disabled={loading}
                className="w-full bg-[#0a0f1b] border border-slate-800 focus:border-cyan-500/80 rounded-xl py-3 pl-10 pr-10 text-sm text-slate-200 placeholder:text-slate-600 focus:outline-none transition-colors font-mono disabled:opacity-50"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3.5 top-3.5 text-slate-500 hover:text-slate-300 transition-colors"
                title={showPassword ? 'Hide Key' : 'Show Key'}
              >
                {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 rounded-xl bg-gradient-to-r from-cyan-600 to-emerald-600 hover:from-cyan-500 hover:to-emerald-500 font-semibold text-sm text-white shadow-glow-cyan flex items-center justify-center gap-2 transition-all disabled:opacity-50 cursor-pointer"
          >
            {loading ? (
              <span className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
            ) : (
              <>
                <span>Authenticate & Connect</span>
                <ArrowRight className="w-4 h-4" />
              </>
            )}
          </button>
        </form>

        <div className="mt-8 pt-6 border-t border-slate-800/80 text-center space-y-2">
          <p className="text-[11px] text-slate-400 font-mono flex items-center justify-center gap-1.5">
            <Lock className="w-3 h-3 text-cyan-400" />
            <span>Secure connection required. Use an authorized SecureOps API credential.</span>
          </p>
          <p className="text-[10px] text-slate-500 font-mono">
            Credentials are transmitted only to your configured SecureOps gateway.
          </p>
        </div>
      </motion.div>
    </div>
  );
};
