import React from 'react';
import {
  Stethoscope,
  FileText,
  Sparkles,
  BookOpen,
  Sun,
  Type,
  Eye,
  History,
  LogOut,
  PanelLeft,
  PanelRight,
  UserCircle,
} from 'lucide-react';
import { AccessibilitySettings } from '../types';
import { AuthUser } from '../api';

interface HeaderProps {
  accessibility: AccessibilitySettings;
  setAccessibility: React.Dispatch<React.SetStateAction<AccessibilitySettings>>;
  onOpenDoctorSummary: () => void;
  onOpenSampleCases: () => void;
  onOpenBodyExplorer: () => void;
  citationCount: number;
  isHistoryOpen: boolean;
  onToggleHistory: () => void;
  isCitationsOpen: boolean;
  onToggleCitations: () => void;
  authUser: AuthUser;
  onLogout: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  accessibility,
  setAccessibility,
  onOpenDoctorSummary,
  onOpenSampleCases,
  onOpenBodyExplorer,
  citationCount,
  isHistoryOpen,
  onToggleHistory,
  isCitationsOpen,
  onToggleCitations,
  authUser,
  onLogout,
}) => {
  const cycleFontSize = () => {
    if (accessibility.fontSize === 'normal') setAccessibility(a => ({ ...a, fontSize: 'large' }));
    else if (accessibility.fontSize === 'large') setAccessibility(a => ({ ...a, fontSize: 'xlarge' }));
    else setAccessibility(a => ({ ...a, fontSize: 'normal' }));
  };

  return (
    <header className="sticky top-0 z-30 bg-white/95 backdrop-blur border-b border-slate-200 text-slate-900 shadow-sm shrink-0">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between gap-2">
        {/* Left Section: Sidebar Toggle & Brand */}
        <div className="flex items-center gap-2.5">
          {/* History Sidebar Toggle Button (Left Edge) */}
          <button
            onClick={onToggleHistory}
            className={`p-2 rounded-xl text-xs font-semibold flex items-center gap-1.5 transition-all ${
              isHistoryOpen
                ? 'bg-teal-100 text-teal-800 border border-teal-300 shadow-2xs'
                : 'bg-slate-100 hover:bg-slate-200/80 text-slate-700 border border-slate-200'
            }`}
            title="Mở/Đóng Lịch sử trò chuyện (Chat History)"
          >
            <PanelLeft className="w-4 h-4 text-teal-700" />
            <History className="w-4 h-4 hidden sm:inline" />
            <span className="hidden md:inline font-bold">Lịch Sử</span>
          </button>

          {/* Logo & Brand */}
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-teal-600 to-emerald-500 flex items-center justify-center text-white font-bold shadow-md shadow-teal-600/20 shrink-0">
              <Stethoscope className="w-5 h-5 stroke-[2.2]" />
            </div>
            <div>
              <div className="flex items-center gap-1.5">
                <h1 className="text-base sm:text-lg font-bold tracking-tight text-slate-900 flex items-center gap-1.5">
                  DermaCare <span className="text-[10px] sm:text-xs font-semibold px-2 py-0.5 rounded-full bg-teal-50 text-teal-700 border border-teal-200">AI Assistant</span>
                </h1>
              </div>
              <p className="text-[11px] text-slate-500 hidden xl:block">
                Tư vấn sức khỏe làn da dựa trên bằng chứng y khoa
              </p>
            </div>
          </div>
        </div>

        {/* Center Quick Features */}
        <div className="hidden md:flex items-center gap-1.5">
          <button
            onClick={onOpenBodyExplorer}
            className="px-3 py-1.5 rounded-xl text-xs font-semibold text-slate-700 bg-slate-100 hover:bg-slate-200/80 border border-slate-200 transition-all flex items-center gap-1.5"
          >
            <Eye className="w-3.5 h-3.5 text-teal-600" />
            Vùng Da (Zone Map)
          </button>

          <button
            onClick={onOpenSampleCases}
            className="hidden lg:flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold bg-teal-50 hover:bg-teal-100 text-teal-800 border border-teal-200 transition-all"
            title="Xem các ca bệnh lâm sàng mẫu"
          >
            <Sparkles className="w-3.5 h-3.5 text-teal-600" />
            Ca Lâm Sàng Mẫu
          </button>
        </div>

        {/* Right Section: Citations Sidebar Toggle, Report & Accessibility Controls */}
        <div className="flex items-center gap-2">
          {/* Export Doctor Visit Summary */}
          <button
            onClick={onOpenDoctorSummary}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-bold bg-emerald-600 hover:bg-emerald-700 text-white shadow-xs transition-all shrink-0"
            title="Xuất báo cáo tổng hợp cho bác sĩ"
          >
            <FileText className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Báo Cáo Bác Sĩ</span>
            <span className="sm:hidden">Báo Cáo</span>
          </button>

          {/* Citations Sidebar Toggle Button (Right Edge) */}
          <button
            onClick={onToggleCitations}
            className={`p-2 rounded-xl text-xs font-semibold flex items-center gap-1.5 transition-all ${
              isCitationsOpen
                ? 'bg-teal-100 text-teal-800 border border-teal-300 shadow-2xs'
                : 'bg-slate-100 hover:bg-slate-200/80 text-slate-700 border border-slate-200'
            }`}
            title="Mở/Đóng Trích dẫn tài liệu y khoa (Medical Citations)"
          >
            <BookOpen className="w-4 h-4 text-teal-700" />
            <span className="hidden md:inline font-bold">Trích Dẫn</span>
            {citationCount > 0 && (
              <span className="px-1.5 py-0.2 rounded-full text-[10px] bg-teal-600 text-white font-bold">
                {citationCount}
              </span>
            )}
            <PanelRight className="w-4 h-4 text-teal-700" />
          </button>

          {/* Accessibility Settings */}
          <div className="hidden sm:flex items-center border-l border-slate-200 pl-2 ml-0.5 gap-1">
            <button
              onClick={cycleFontSize}
              className={`p-1.5 rounded-lg text-xs font-semibold transition-all ${
                accessibility.fontSize !== 'normal'
                  ? 'bg-teal-100 text-teal-800 border border-teal-300'
                  : 'text-slate-500 hover:text-slate-900 hover:bg-slate-100'
              }`}
              title={`Font Size: ${accessibility.fontSize.toUpperCase()}`}
            >
              <Type className="w-4 h-4" />
            </button>

            <button
              onClick={() => setAccessibility(a => ({ ...a, highContrast: !a.highContrast }))}
              className={`p-1.5 rounded-lg transition-all ${
                accessibility.highContrast
                  ? 'bg-amber-100 text-amber-800 border border-amber-300'
                  : 'text-slate-500 hover:text-slate-900 hover:bg-slate-100'
              }`}
              title="Chế độ Tương phản cao"
            >
              <Sun className="w-4 h-4" />
            </button>

            <button
              onClick={() => setAccessibility(a => ({ ...a, dyslexicFont: !a.dyslexicFont }))}
              className={`p-1.5 rounded-lg text-xs font-bold transition-all ${
                accessibility.dyslexicFont
                  ? 'bg-purple-100 text-purple-800 border border-purple-300'
                  : 'text-slate-500 hover:text-slate-900 hover:bg-slate-100'
              }`}
              title="Phông chữ dễ đọc"
            >
              Aa
            </button>
          </div>

          <div className="flex items-center gap-1.5 border-l border-slate-200 pl-2 ml-0.5">
            <div className="hidden xl:flex items-center gap-1.5 text-xs font-semibold text-slate-600 max-w-44">
              <UserCircle className="w-4 h-4 text-teal-700 shrink-0" />
              <span className="truncate">{authUser.email}</span>
            </div>
            <button
              onClick={onLogout}
              className="p-1.5 rounded-lg text-slate-500 hover:text-slate-900 hover:bg-slate-100 transition-all"
              title="Đăng xuất"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </header>
  );
};
