import React, { useState } from 'react';
import {
  MessageSquare,
  Plus,
  Trash2,
  X,
  History,
  Globe2,
  Lock,
  Search,
  PanelLeftClose,
  Clock,
  ShieldCheck,
  RotateCcw
} from 'lucide-react';
import { ChatSession } from '../types';

interface ChatHistorySidebarProps {
  sessions: ChatSession[];
  activeSessionId: string;
  onSelectSession: (id: string) => void;
  onNewChat: () => void;
  onDeleteSession: (id: string) => void;
  onClearAllHistory: () => void;
  onTogglePublic: (id: string, isPublic: boolean) => void;
  isOpen: boolean;
  onToggleOpen: () => void;
}

export const ChatHistorySidebar: React.FC<ChatHistorySidebarProps> = ({
  sessions,
  activeSessionId,
  onSelectSession,
  onNewChat,
  onDeleteSession,
  onClearAllHistory,
  onTogglePublic,
  isOpen,
  onToggleOpen,
}) => {
  const [searchTerm, setSearchTerm] = useState('');

  const filteredSessions = sessions.filter((s) => {
    const term = searchTerm.toLowerCase();
    return (
      s.title.toLowerCase().includes(term) ||
      s.messages.some((m) => m.content.toLowerCase().includes(term))
    );
  });

  if (!isOpen) {
    return null;
  }

  return (
    <>
      {/* Mobile Overlay Backdrop */}
      <div
        className="lg:hidden fixed inset-0 bg-slate-900/50 backdrop-blur-xs z-40"
        onClick={onToggleOpen}
      />

      {/* Sidebar Container - Left Edge */}
      <aside
        className={`fixed lg:static inset-y-0 left-0 z-40 w-72 sm:w-80 bg-white border-r border-slate-200 flex flex-col h-full min-h-0 shrink-0 shadow-xl lg:shadow-none transition-all duration-300 ease-in-out`}
      >
        {/* Header */}
        <div className="p-4 border-b border-slate-200 bg-slate-50/80 flex items-center justify-between gap-2 shrink-0">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-teal-100 text-teal-700 flex items-center justify-center font-semibold">
              <History className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-sm font-bold text-slate-900 leading-none">Lịch Sử Trò Chuyện</h2>
              <p className="text-[11px] text-slate-500 font-medium mt-0.5">Consultation History</p>
            </div>
          </div>

          <button
            onClick={onToggleOpen}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-200/60 transition-colors"
            title="Đóng sidebar lịch sử"
          >
            <PanelLeftClose className="w-4 h-4 hidden lg:block" />
            <X className="w-4 h-4 lg:hidden" />
          </button>
        </div>

        {/* Action: New Chat Button */}
        <div className="p-3 border-b border-slate-200 bg-white shrink-0">
          <button
            onClick={onNewChat}
            className="w-full py-2.5 px-3.5 rounded-xl bg-teal-600 hover:bg-teal-700 text-white font-bold text-xs flex items-center justify-center gap-2 shadow-xs transition-all active:scale-[0.99]"
          >
            <Plus className="w-4 h-4 stroke-[2.5]" />
            <span>Cuộc Trò Chuyện Mới</span>
          </button>
        </div>

        {/* Search Bar */}
        <div className="p-3 border-b border-slate-200 bg-white shrink-0">
          <div className="relative">
            <Search className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-2.5" />
            <input
              type="text"
              placeholder="Tìm kiếm cuộc trò chuyện..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-8 pr-3 py-1.5 text-xs bg-slate-100 border border-slate-200 rounded-lg focus:outline-none focus:border-teal-500 focus:bg-white text-slate-800 placeholder-slate-400"
            />
          </div>
        </div>

        {/* Sessions List Feed */}
        <div className="flex-1 overflow-y-auto min-h-0 p-2.5 space-y-1.5">
          {filteredSessions.length === 0 ? (
            <div className="p-6 text-center text-slate-400 text-xs space-y-2">
              <MessageSquare className="w-8 h-8 mx-auto text-slate-300" />
              <p className="font-medium text-slate-500">Chưa có lịch sử cuộc trò chuyện</p>
              <p className="text-[11px] text-slate-400">Bắt đầu một cuộc trò chuyện mới để lưu tại đây.</p>
            </div>
          ) : (
            filteredSessions.map((session) => {
              const isActive = session.id === activeSessionId;
              const msgCount = session.messages.length;
              const userMsg = session.messages.find((m) => m.role === 'user');
              const preview = userMsg ? userMsg.content : session.title;

              return (
                <div
                  key={session.id}
                  onClick={() => onSelectSession(session.id)}
                  className={`group relative p-3 rounded-xl border text-xs cursor-pointer transition-all flex flex-col justify-between gap-1.5 ${
                    isActive
                      ? 'bg-teal-50/90 border-teal-300 text-teal-900 shadow-2xs font-medium'
                      : 'bg-white hover:bg-slate-50 border-slate-200 text-slate-700 hover:border-slate-300'
                  }`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex items-center gap-1.5 text-slate-900 font-bold truncate pr-4">
                      <MessageSquare className={`w-3.5 h-3.5 shrink-0 ${isActive ? 'text-teal-600' : 'text-slate-400'}`} />
                      <span className="truncate">{session.title}</span>
                    </div>

                    <div className="flex items-center gap-0.5 shrink-0">
                      {session.canEdit === false ? (
                        session.isPublic && <Globe2 className="w-3.5 h-3.5 text-teal-600" aria-label="Public" />
                      ) : (
                        <>
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              onTogglePublic(session.id, !session.isPublic);
                            }}
                            className="opacity-0 group-hover:opacity-100 p-1 rounded hover:bg-teal-50 text-slate-400 hover:text-teal-700 transition-all"
                            title={session.isPublic ? 'Chuyển về riêng tư' : 'Chia sẻ public'}
                          >
                            {session.isPublic ? <Globe2 className="w-3.5 h-3.5" /> : <Lock className="w-3.5 h-3.5" />}
                          </button>
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              onDeleteSession(session.id);
                            }}
                            className="opacity-0 group-hover:opacity-100 p-1 rounded hover:bg-red-50 text-slate-400 hover:text-red-600 transition-all"
                            title="Xóa cuộc trò chuyện"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </>
                      )}
                    </div>
                  </div>

                  <p className="text-[11px] text-slate-500 line-clamp-1 font-normal">
                    {preview}
                  </p>

                  <div className="flex items-center justify-between text-[10px] text-slate-400 pt-1 border-t border-slate-100">
                    <span className="flex items-center gap-1">
                      <Clock className="w-3 h-3 text-slate-400" />
                      {session.updatedAt}
                    </span>
                    <span className="bg-slate-100 font-semibold px-1.5 py-0.2 rounded text-slate-600 border border-slate-200">
                      {msgCount} tin nhắn
                    </span>
                  </div>
                </div>
              );
            })
          )}
        </div>

        {/* Footer Actions */}
        <div className="p-3 border-t border-slate-200 bg-slate-50/80 shrink-0 space-y-2">
          {sessions.length > 0 && (
            <button
              onClick={onClearAllHistory}
              className="w-full py-1.5 px-2 rounded-lg text-slate-500 hover:text-red-600 hover:bg-red-50 text-[11px] font-semibold flex items-center justify-center gap-1.5 transition-colors border border-transparent hover:border-red-200"
            >
              <RotateCcw className="w-3 h-3" />
              <span>Xóa toàn bộ lịch sử</span>
            </button>
          )}

          <div className="text-[10px] text-slate-400 flex items-center gap-1.5 justify-center">
            <ShieldCheck className="w-3.5 h-3.5 text-teal-600 shrink-0" />
            <span>Lưu an toàn trên trình duyệt</span>
          </div>
        </div>
      </aside>
    </>
  );
};
