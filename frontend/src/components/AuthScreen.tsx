import React, { useState } from 'react';
import { Eye, EyeOff, Loader2, LogIn, Stethoscope, UserPlus } from 'lucide-react';
import { AuthUser, signIn, signUp } from '../api';

interface AuthScreenProps {
  onAuthenticated: (user: AuthUser) => void;
}

export const AuthScreen: React.FC<AuthScreenProps> = ({ onAuthenticated }) => {
  const [mode, setMode] = useState<'login' | 'register'>('login');
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const isRegister = mode === 'register';

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setError('');
    setIsSubmitting(true);

    try {
      const user = isRegister ? await signUp(email.trim(), password, name.trim()) : await signIn(email.trim(), password);
      onAuthenticated(user);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Không thể xác thực tài khoản.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 flex items-center justify-center px-4 py-8 font-sans antialiased selection:bg-teal-200 selection:text-teal-900">
      <main className="w-full max-w-md bg-white border border-slate-200 rounded-2xl shadow-xl shadow-slate-200/70 overflow-hidden">
        <div className="px-6 pt-6 pb-5 border-b border-slate-100">
          <div className="flex items-center gap-3">
            <div className="w-11 h-11 rounded-xl bg-gradient-to-tr from-teal-600 to-emerald-500 flex items-center justify-center text-white shadow-md shadow-teal-600/20">
              <Stethoscope className="w-6 h-6 stroke-[2.2]" />
            </div>
            <div>
              <h1 className="text-xl font-bold tracking-tight text-slate-900">DermaCare AI</h1>
              <p className="text-xs font-medium text-slate-500">Truy cập trợ lý tư vấn da liễu</p>
            </div>
          </div>
        </div>

        <div className="p-6">
          <div className="grid grid-cols-2 gap-1 rounded-xl bg-slate-100 p-1 mb-5">
            <button
              type="button"
              onClick={() => {
                setMode('login');
                setError('');
              }}
              className={`h-10 rounded-lg text-sm font-bold transition-all flex items-center justify-center gap-2 ${
                !isRegister ? 'bg-white text-teal-800 shadow-xs' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <LogIn className="w-4 h-4" />
              Đăng nhập
            </button>
            <button
              type="button"
              onClick={() => {
                setMode('register');
                setError('');
              }}
              className={`h-10 rounded-lg text-sm font-bold transition-all flex items-center justify-center gap-2 ${
                isRegister ? 'bg-white text-teal-800 shadow-xs' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <UserPlus className="w-4 h-4" />
              Đăng ký
            </button>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            {isRegister && (
              <label className="block">
                <span className="text-xs font-bold text-slate-700">Họ tên</span>
                <input
                  value={name}
                  onChange={(event) => setName(event.target.value)}
                  required={isRegister}
                  autoComplete="name"
                  className="mt-1.5 w-full h-11 rounded-xl border border-slate-200 bg-slate-50 px-3 text-sm text-slate-900 outline-none transition-all focus:border-teal-500 focus:bg-white"
                  placeholder="Nguyễn Văn A"
                />
              </label>
            )}

            <label className="block">
              <span className="text-xs font-bold text-slate-700">Email</span>
              <input
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                required
                type="email"
                autoComplete="email"
                className="mt-1.5 w-full h-11 rounded-xl border border-slate-200 bg-slate-50 px-3 text-sm text-slate-900 outline-none transition-all focus:border-teal-500 focus:bg-white"
                placeholder="you@example.com"
              />
            </label>

            <label className="block">
              <span className="text-xs font-bold text-slate-700">Mật khẩu</span>
              <div className="mt-1.5 flex items-center rounded-xl border border-slate-200 bg-slate-50 focus-within:border-teal-500 focus-within:bg-white">
                <input
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  required
                  minLength={6}
                  type={showPassword ? 'text' : 'password'}
                  autoComplete={isRegister ? 'new-password' : 'current-password'}
                  className="min-w-0 flex-1 h-11 bg-transparent px-3 text-sm text-slate-900 outline-none"
                  placeholder="Tối thiểu 6 ký tự"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword((value) => !value)}
                  className="mr-1.5 p-2 rounded-lg text-slate-500 hover:bg-slate-100 hover:text-slate-900"
                  title={showPassword ? 'Ẩn mật khẩu' : 'Hiện mật khẩu'}
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </label>

            {error && (
              <div className="rounded-xl border border-rose-200 bg-rose-50 px-3 py-2 text-xs font-medium text-rose-800">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full h-11 rounded-xl bg-teal-600 hover:bg-teal-700 disabled:opacity-60 text-white text-sm font-bold transition-all shadow-xs flex items-center justify-center gap-2"
            >
              {isSubmitting ? <Loader2 className="w-4 h-4 animate-spin" /> : isRegister ? <UserPlus className="w-4 h-4" /> : <LogIn className="w-4 h-4" />}
              {isRegister ? 'Tạo tài khoản' : 'Đăng nhập'}
            </button>
          </form>
        </div>
      </main>
    </div>
  );
};
