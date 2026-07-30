/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useState, useRef, useEffect } from 'react';
import { Header } from './components/Header';
import { DisclaimerBanner } from './components/DisclaimerBanner';
import { ChatMessageItem } from './components/ChatMessageItem';
import { CitationsSidebar } from './components/CitationsSidebar';
import { ChatHistorySidebar } from './components/ChatHistorySidebar';
import { ImageUploader } from './components/ImageUploader';
import { SymptomWizard } from './components/SymptomWizard';
import { DoctorSummaryModal } from './components/DoctorSummaryModal';
import { BodyExplorerModal } from './components/BodyExplorerModal';
import { SampleCasesDrawer } from './components/SampleCasesDrawer';
import { AuthScreen } from './components/AuthScreen';
import { ChatMessage, Citation, SymptomFilter, AccessibilitySettings, SampleCase, ChatSession } from './types';
import { SAMPLE_CASES, INITIAL_CITATIONS } from './data/sampleCases';
import { Send, Image as ImageIcon, Sliders, Sparkles, RefreshCw, Bot, HeartHandshake, ShieldCheck } from 'lucide-react';
import { AuthUser, clearConversations, clearStoredAuth, deleteConversation, getStoredAuthUser, listConversations, sendChatMessage, updateConversation } from './api';

const STORAGE_KEY_SESSIONS = 'dermacare_chat_sessions_v2';
const STORAGE_KEY_ACTIVE_ID = 'dermacare_active_session_id_v2';

const createDefaultSession = (): ChatSession => {
  const defaultId = `session-${Date.now()}`;
  return {
    id: defaultId,
    title: 'Tư Vấn Da Liễu Ban Đầu',
    isPublic: false,
    createdAt: new Date().toLocaleDateString(),
    updatedAt: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    messages: [
      {
        id: 'welcome-01',
        role: 'assistant',
        content: `Xin chào! Tôi là DermaCare AI, trợ lý tư vấn sức khỏe làn da dựa trên bằng chứng y khoa.

Tôi ở đây để hỗ trợ giải đáp thắc mắc về các vấn đề da liễu, phân tích ảnh chụp tổn thương da và cung cấp tài liệu hướng dẫn y khoa.

Bạn cần trợ giúp gì hôm nay? Hãy nhập câu hỏi hoặc gửi hình ảnh bên dưới.`,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        citations: INITIAL_CITATIONS.slice(0, 2),
      },
    ],
  };
};

const isTemporarySession = (id: string) => id.startsWith('session-');
const withWelcomeMessage = (session: ChatSession): ChatSession =>
  session.messages.length > 0 ? session : { ...session, messages: createDefaultSession().messages };
const hasUserMessages = (session: ChatSession) => session.messages.some((message) => message.role === 'user');
const scopedStorageKey = (base: string, user: AuthUser | null) => `${base}:${user?.id || 'guest'}`;
const loadStoredSessions = (user: AuthUser | null): ChatSession[] => {
  try {
    const saved = localStorage.getItem(scopedStorageKey(STORAGE_KEY_SESSIONS, user));
    if (saved) {
      const parsed = JSON.parse(saved);
      if (Array.isArray(parsed) && parsed.length > 0) return parsed;
    }
  } catch (e) {
    console.warn('Could not parse chat sessions:', e);
  }
  return [createDefaultSession()];
};
const loadStoredActiveId = (user: AuthUser | null) => {
  try {
    return localStorage.getItem(scopedStorageKey(STORAGE_KEY_ACTIVE_ID, user));
  } catch {
    return null;
  }
};
const latestCitationsFor = (session: ChatSession): Citation[] =>
  [...session.messages].reverse().find((message) => message.role === 'assistant' && message.citations !== undefined)?.citations || [];

export default function App() {
  const [authUser, setAuthUser] = useState<AuthUser | null>(() => getStoredAuthUser());

  // Sidebar Open States (Left & Right)
  const [isHistoryOpen, setIsHistoryOpen] = useState(true);
  const [isCitationsOpen, setIsCitationsOpen] = useState(true);

  // Accessibility State
  const [accessibility, setAccessibility] = useState<AccessibilitySettings>({
    fontSize: 'normal',
    highContrast: false,
    dyslexicFont: false,
  });

  // Sessions State Management
  const [sessions, setSessions] = useState<ChatSession[]>(() => loadStoredSessions(getStoredAuthUser()));

  const [activeSessionId, setActiveSessionId] = useState<string>(() => {
    const savedId = loadStoredActiveId(getStoredAuthUser());
    if (savedId) return savedId;
    return sessions[0]?.id || `session-${Date.now()}`;
  });

  // Current Active Session
  const currentSession = sessions.find((s) => s.id === activeSessionId) || sessions[0] || createDefaultSession();
  const messages = currentSession.messages;
  const currentCitations = latestCitationsFor(currentSession);

  useEffect(() => {
    if (!authUser) return;
    const localSessions = loadStoredSessions(authUser);
    const localActiveId = loadStoredActiveId(authUser);
    setSessions(localSessions);
    setActiveSessionId(localActiveId && localSessions.some((session) => session.id === localActiveId) ? localActiveId : localSessions[0].id);
  }, [authUser?.id]);

  // Persist sessions to LocalStorage
  useEffect(() => {
    if (!authUser) return;
    try {
      localStorage.setItem(scopedStorageKey(STORAGE_KEY_SESSIONS, authUser), JSON.stringify(sessions));
      localStorage.setItem(scopedStorageKey(STORAGE_KEY_ACTIVE_ID, authUser), activeSessionId);
    } catch (e) {
      console.warn('Could not save sessions to storage:', e);
    }
  }, [sessions, activeSessionId, authUser]);

  useEffect(() => {
    if (!authUser) return;

    let cancelled = false;

    listConversations()
      .then((serverSessions) => {
        if (cancelled || serverSessions.length === 0) return;
        const hydrated = serverSessions.map(withWelcomeMessage);
        setSessions(hydrated);
        setActiveSessionId((current) => (hydrated.some((s) => s.id === current) ? current : hydrated[0].id));
      })
      .catch((e) => console.warn('Could not load backend sessions:', e));

    return () => {
      cancelled = true;
    };
  }, [authUser]);

  const handleLogout = () => {
    clearStoredAuth();
    const fresh = createDefaultSession();
    setSessions([fresh]);
    setActiveSessionId(fresh.id);
    setAuthUser(null);
  };

  const [inputPrompt, setInputPrompt] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [selectedImage, setSelectedImage] = useState<string | null>(null);
  const [imageFile, setImageFile] = useState<File | null>(null);

  // Symptom Filter Wizard
  const [symptoms, setSymptoms] = useState<SymptomFilter>({
    location: '',
    duration: '',
    itchLevel: 0,
    painLevel: 0,
    isSpreading: false,
    additionalNotes: '',
  });
  const [showSymptomWizard, setShowSymptomWizard] = useState(false);

  // Citations Selection
  const [selectedCitation, setSelectedCitation] = useState<Citation | null>(null);

  // Modals
  const [showDoctorReportModal, setShowDoctorReportModal] = useState(false);
  const [showSampleCasesModal, setShowSampleCasesModal] = useState(false);
  const [showBodyExplorerModal, setShowBodyExplorerModal] = useState(false);

  // Report Items Saved
  const [reportMessageIds, setReportMessageIds] = useState<Set<string>>(new Set());

  // Scroll Ref
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  // Session Action Handlers
  const handleSelectSession = (id: string) => {
    setActiveSessionId(id);
  };

  const handleNewChat = async () => {
    const emptySession = sessions.find((session) => !hasUserMessages(session));
    if (emptySession) {
      setActiveSessionId(emptySession.id);
      return;
    }

    const fresh = createDefaultSession();
    setSessions((prev) => [fresh, ...prev.filter(hasUserMessages)]);
    setActiveSessionId(fresh.id);
  };

  const handleDeleteSession = (id: string) => {
    const session = sessions.find((s) => s.id === id);
    if (session?.canEdit === false) return;

    if (!isTemporarySession(id)) {
      deleteConversation(id).catch((e) => console.warn('Could not delete backend session:', e));
    }

    setSessions((prev) => {
      const filtered = prev.filter((s) => s.id !== id);
      if (filtered.length === 0) {
        const fresh = createDefaultSession();
        setActiveSessionId(fresh.id);
        return [fresh];
      }
      if (id === activeSessionId) {
        setActiveSessionId(filtered[0].id);
      }
      return filtered;
    });
  };

  const handleClearAllHistory = () => {
    clearConversations().catch((e) => console.warn('Could not clear backend sessions:', e));
    const fresh = createDefaultSession();
    setSessions([fresh]);
    setActiveSessionId(fresh.id);
  };

  const handleTogglePublic = (id: string, isPublic: boolean) => {
    const session = sessions.find((s) => s.id === id);
    if (!session || session.canEdit === false) return;

    setSessions((prev) => prev.map((s) => (s.id === id ? { ...s, isPublic } : s)));
    if (!isTemporarySession(id)) {
      updateConversation(id, { isPublic }).catch((e) => {
        console.warn('Could not update conversation visibility:', e);
        setSessions((prev) => prev.map((s) => (s.id === id ? { ...s, isPublic: !isPublic } : s)));
      });
    }
  };

  // Handle Image Selection
  const handleImageSelected = (base64Url: string, file: File) => {
    setSelectedImage(base64Url);
    setImageFile(file);
  };

  const handleClearImage = () => {
    setSelectedImage(null);
    setImageFile(null);
  };

  // Handle Sample Case Trigger
  const handleSelectSampleCase = (sample: SampleCase) => {
    setShowSampleCasesModal(false);
    setSelectedImage(sample.imageUrl);
    setSymptoms({
      location: sample.symptoms.location,
      duration: sample.symptoms.duration,
      itchLevel: sample.symptoms.itchLevel,
      painLevel: sample.symptoms.painLevel,
      isSpreading: sample.symptoms.isSpreading,
      additionalNotes: '',
    });
    setInputPrompt(sample.promptText);
  };

  // Handle Adding to Doctor Report
  const handleToggleReportMessage = (msg: ChatMessage) => {
    setReportMessageIds((prev) => {
      const next = new Set(prev);
      if (next.has(msg.id)) {
        next.delete(msg.id);
      } else {
        next.add(msg.id);
      }
      return next;
    });
  };

  // Submit Inquiry to AI Server
  const handleSendMessage = async (overridePrompt?: string) => {
    const promptToSend = overridePrompt || inputPrompt;
    if (!promptToSend.trim() && !selectedImage) return;

    const userMessageId = `user-${Date.now()}`;
    const userMsg: ChatMessage = {
      id: userMessageId,
      role: 'user',
      content: promptToSend.trim() || 'Phân tích hình ảnh tổn thương da đính kèm.',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      image: selectedImage
        ? {
            url: selectedImage,
            name: imageFile?.name || 'Ảnh tổn thương da',
          }
        : undefined,
      symptomSummary: symptoms.location ? { ...symptoms } : undefined,
    };

    // Calculate new session title if default
    const isDefaultTitle =
      currentSession.title.startsWith('Tư Vấn Da Liễu Ban Đầu') ||
      currentSession.title.startsWith('Tư Vấn Da Liễu');
    const newTitle = isDefaultTitle
      ? promptToSend.slice(0, 26) + (promptToSend.length > 26 ? '...' : '')
      : currentSession.title;

    const updatedWithUser = [...currentSession.messages, userMsg];

    setSessions((prev) =>
      prev.map((s) => {
        if (s.id === currentSession.id) {
          return {
            ...s,
            title: newTitle,
            updatedAt: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
            messages: updatedWithUser,
          };
        }
        return s;
      })
    );

    setInputPrompt('');
    setIsLoading(true);

    const currentImage = selectedImage;
    const currentMimeType = imageFile?.type || 'image/jpeg';
    const currentSymptoms = { ...symptoms };

    // Reset local attached image & symptoms after sending
    setSelectedImage(null);
    setImageFile(null);

    try {
      const data = await sendChatMessage({
        conversationId: isTemporarySession(currentSession.id) ? undefined : currentSession.id,
        message: promptToSend,
        imageBase64: currentImage,
        mimeType: currentMimeType,
        symptomSummary: currentSymptoms.location ? currentSymptoms : undefined,
        history: currentSession.messages.map((m) => ({ role: m.role, content: m.content })),
      });

      const aiMessageId = `ai-${Date.now()}`;
      const newCitations: Citation[] = (data.citations as Citation[]) || INITIAL_CITATIONS.slice(0, 2);

      const assistantMsg: ChatMessage = {
        id: aiMessageId,
        role: 'assistant',
        content: data.text || 'Tôi đã hoàn thành phân tích. Hãy tham khảo ý kiến bác sĩ chuyên khoa da liễu để nhận chẩn đoán trực tiếp.',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        citations: newCitations,
      };

      if (data.conversation) {
        setSessions((prev) => {
          const updated = prev.map((s) =>
            s.id === currentSession.id || s.id === data.conversation.id ? data.conversation : s
          );
          return updated.some((s) => s.id === data.conversation.id) ? updated : [data.conversation, ...updated];
        });
        setActiveSessionId(data.conversation.id);
      } else {
        setSessions((prev) =>
          prev.map((s) => {
            if (s.id === currentSession.id) {
              return {
                ...s,
                updatedAt: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
                messages: [...s.messages, assistantMsg],
              };
            }
            return s;
          })
        );
      }
    } catch (error) {
      console.error('Error querying chat API:', error);
      const errorMsg: ChatMessage = {
        id: `err-${Date.now()}`,
        role: 'assistant',
        content: `Rất tiếc, đã có sự cố kết nối trong quá trình xử lý câu hỏi của bạn.

Vui lòng kiểm tra lại kết nối mạng. Nếu bạn có biểu hiện da liễu cấp tính, hãy đến gặp bác sĩ chuyên khoa ngay.`,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        citations: INITIAL_CITATIONS.slice(0, 1),
      };

      setSessions((prev) =>
        prev.map((s) => {
          if (s.id === currentSession.id) {
            return {
              ...s,
              updatedAt: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
              messages: [...s.messages, errorMsg],
            };
          }
          return s;
        })
      );
    } finally {
      setIsLoading(false);
    }
  };

  // Font Size CSS utility
  const getFontSizeClass = () => {
    if (accessibility.fontSize === 'large') return 'text-base';
    if (accessibility.fontSize === 'xlarge') return 'text-lg';
    return 'text-sm';
  };

  if (!authUser) {
    return <AuthScreen onAuthenticated={setAuthUser} />;
  }

  return (
    <div
      className={`h-screen max-h-screen overflow-hidden bg-slate-50 text-slate-900 flex flex-col font-sans antialiased selection:bg-teal-200 selection:text-teal-900 ${
        accessibility.highContrast ? 'contrast-125 brightness-105' : ''
      } ${accessibility.dyslexicFont ? 'tracking-wide word-spacing-wide' : ''}`}
    >
      {/* Header */}
      <Header
        accessibility={accessibility}
        setAccessibility={setAccessibility}
        onOpenDoctorSummary={() => setShowDoctorReportModal(true)}
        onOpenSampleCases={() => setShowSampleCasesModal(true)}
        onOpenBodyExplorer={() => setShowBodyExplorerModal(true)}
        citationCount={currentCitations.length}
        isHistoryOpen={isHistoryOpen}
        onToggleHistory={() => setIsHistoryOpen(!isHistoryOpen)}
        isCitationsOpen={isCitationsOpen}
        onToggleCitations={() => setIsCitationsOpen(!isCitationsOpen)}
        authUser={authUser}
        onLogout={handleLogout}
      />

      {/* Persistent Medical Disclaimer Banner */}
      <DisclaimerBanner />

      {/* Main Screen Layout: Left Sidebar + Chat Center + Right Sidebar */}
      <div className="flex-1 max-w-full w-full mx-auto flex overflow-hidden min-h-0 relative">
        {/* Left Sidebar: Chat History */}
        <ChatHistorySidebar
          sessions={sessions}
          activeSessionId={activeSessionId}
          onSelectSession={handleSelectSession}
          onNewChat={handleNewChat}
          onDeleteSession={handleDeleteSession}
          onClearAllHistory={handleClearAllHistory}
          onTogglePublic={handleTogglePublic}
          isOpen={isHistoryOpen}
          onToggleOpen={() => setIsHistoryOpen(!isHistoryOpen)}
        />

        {/* Center Main Chat Column */}
        <main className="flex-1 flex flex-col min-w-0 min-h-0 bg-slate-100/50 relative">
          {/* Quick Prompt Starters Bar when feed is short */}
          {messages.length <= 2 && (
            <div className="p-4 bg-white border-b border-slate-200 shrink-0">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-bold text-teal-900 flex items-center gap-1.5">
                  <HeartHandshake className="w-4 h-4 text-teal-600" />
                  Chủ Đề Phổ Biến
                </span>
                <button
                  onClick={() => setShowSampleCasesModal(true)}
                  className="text-xs text-teal-700 hover:text-teal-900 underline flex items-center gap-1 font-semibold"
                >
                  <Sparkles className="w-3 h-3 text-teal-600" />
                  Thử Ảnh Ca Bệnh Mẫu
                </button>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 text-xs">
                <button
                  onClick={() => handleSendMessage('Phân biệt giữa Chàm (Eczema) và Viêm da tiếp xúc?')}
                  className="p-2.5 rounded-xl bg-slate-50 hover:bg-teal-50 border border-slate-200 text-left text-slate-800 hover:text-teal-900 font-medium transition-all flex items-center justify-between group shadow-2xs"
                >
                  <span>Chàm vs Viêm Da Tiếp Xúc</span>
                  <Sparkles className="w-3.5 h-3.5 text-slate-400 group-hover:text-teal-600" />
                </button>

                <button
                  onClick={() => handleSendMessage('Quy tắc ABCDE kiểm tra nốt ruồi bất thường là gì?')}
                  className="p-2.5 rounded-xl bg-slate-50 hover:bg-teal-50 border border-slate-200 text-left text-slate-800 hover:text-teal-900 font-medium transition-all flex items-center justify-between group shadow-2xs"
                >
                  <span>Quy Tắc ABCDE Nốt Ruồi</span>
                  <Sparkles className="w-3.5 h-3.5 text-slate-400 group-hover:text-teal-600" />
                </button>

                <button
                  onClick={() => handleSendMessage('Cách phục hồi hàng rào bảo vệ da khô ngứa mùa đông?')}
                  className="p-2.5 rounded-xl bg-slate-50 hover:bg-teal-50 border border-slate-200 text-left text-slate-800 hover:text-teal-900 font-medium transition-all flex items-center justify-between group shadow-2xs"
                >
                  <span>Phục Hồi Hàng Rào Bảo Vệ Da</span>
                  <Sparkles className="w-3.5 h-3.5 text-slate-400 group-hover:text-teal-600" />
                </button>
              </div>
            </div>
          )}

          {/* Chat Messages Feed with Overflow Scroll */}
          <div className={`flex-1 overflow-y-auto min-h-0 p-4 sm:p-6 space-y-4 ${getFontSizeClass()}`}>
            {messages.map((msg) => (
              <ChatMessageItem
                key={msg.id}
                message={msg}
                onSelectCitation={(cit) => {
                  setSelectedCitation(cit);
                  setIsCitationsOpen(true);
                }}
                onAddToDoctorReport={handleToggleReportMessage}
                isAddedToReport={reportMessageIds.has(msg.id)}
              />
            ))}

            {/* AI Loading Indicator */}
            {isLoading && (
              <div className="flex gap-3 p-4 rounded-2xl bg-white border border-slate-200 items-center shadow-xs">
                <div className="w-8 h-8 rounded-xl bg-teal-100 text-teal-700 flex items-center justify-center animate-pulse">
                  <Bot className="w-5 h-5" />
                </div>
                <div className="flex items-center gap-2 text-xs text-teal-800 font-semibold">
                  <RefreshCw className="w-4 h-4 animate-spin text-teal-600" />
                  <span>Đang phân tích và đối chiếu hướng dẫn y khoa...</span>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Bottom Controls & Input Area */}
          <div className="p-3 sm:p-4 bg-white border-t border-slate-200 space-y-2 shrink-0">
            {/* Attached Photo preview or active symptom badge */}
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div className="flex flex-wrap items-center gap-2">
                {selectedImage && (
                  <div className="flex items-center gap-2 bg-teal-50 border border-teal-300 text-teal-900 text-xs px-2.5 py-1 rounded-lg font-medium">
                    <ImageIcon className="w-3.5 h-3.5 text-teal-600" />
                    <span>Đã đính kèm ảnh</span>
                    <button onClick={handleClearImage} className="text-slate-500 hover:text-slate-900 font-bold ml-1">
                      ×
                    </button>
                  </div>
                )}

                {symptoms.location && (
                  <div className="flex items-center gap-2 bg-slate-100 border border-slate-200 text-slate-800 text-xs px-2.5 py-1 rounded-lg font-medium">
                    <Sliders className="w-3.5 h-3.5 text-teal-600" />
                    <span>
                      Vùng: <strong>{symptoms.location}</strong> ({symptoms.duration || 'Bất kỳ'})
                    </span>
                    <button
                      onClick={() => setSymptoms({ location: '', duration: '', itchLevel: 0, painLevel: 0, isSpreading: false, additionalNotes: '' })}
                      className="text-slate-500 hover:text-slate-900 font-bold ml-1"
                    >
                      ×
                    </button>
                  </div>
                )}
              </div>

              <div className="flex items-center gap-2 text-[11px] text-slate-500 font-medium">
                <ShieldCheck className="w-3.5 h-3.5 text-teal-600" />
                <span>Bảo mật • Không lưu thông tin nhận dạng cá nhân</span>
              </div>
            </div>

            {/* Input Box Row */}
            <div className="relative flex items-end gap-2 bg-slate-50 border border-slate-200 focus-within:border-teal-500 focus-within:bg-white rounded-2xl p-2 transition-all shadow-2xs">
              {/* Image Uploader Popup Trigger / Dropzone */}
              <div className="shrink-0">
                <ImageUploader
                  onImageSelected={handleImageSelected}
                  selectedImage={selectedImage}
                  onClearImage={handleClearImage}
                />
              </div>

              {/* Text Area */}
              <textarea
                value={inputPrompt}
                onChange={(e) => setInputPrompt(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    handleSendMessage();
                  }
                }}
                placeholder="Hỏi về tình trạng da, triệu chứng hoặc gửi ảnh tổn thương da..."
                rows={2}
                className="flex-1 bg-transparent border-none text-slate-900 placeholder-slate-400 text-xs sm:text-sm focus:outline-none resize-none px-2 py-1.5"
              />

              {/* Action Tools */}
              <div className="flex items-center gap-1 shrink-0 pb-1">
                {/* Symptom Wizard Trigger */}
                <button
                  onClick={() => setShowSymptomWizard(!showSymptomWizard)}
                  className={`p-2 rounded-xl text-xs font-medium transition-all ${
                    symptoms.location
                      ? 'bg-teal-100 text-teal-800 border border-teal-300'
                      : 'bg-slate-200/80 hover:bg-slate-200 text-slate-700'
                  }`}
                  title="Thêm chi tiết triệu chứng"
                >
                  <Sliders className="w-4 h-4" />
                </button>

                {/* Send Button */}
                <button
                  onClick={() => handleSendMessage()}
                  disabled={isLoading || (!inputPrompt.trim() && !selectedImage)}
                  className="p-2.5 rounded-xl bg-teal-600 hover:bg-teal-700 disabled:opacity-40 disabled:hover:bg-teal-600 text-white font-semibold transition-all shadow-xs flex items-center justify-center"
                  title="Gửi câu hỏi"
                >
                  <Send className="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>
        </main>

        {/* Right Sidebar: Medical Citations */}
        <CitationsSidebar
          citations={currentCitations}
          selectedCitation={selectedCitation}
          onClearSelectedCitation={() => setSelectedCitation(null)}
          isOpen={isCitationsOpen}
          onToggleOpen={() => setIsCitationsOpen(!isCitationsOpen)}
        />
      </div>

      {/* Symptom Wizard Popover Modal */}
      {showSymptomWizard && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4">
          <SymptomWizard
            symptoms={symptoms}
            setSymptoms={setSymptoms}
            onClose={() => setShowSymptomWizard(false)}
            onApply={() => setShowSymptomWizard(false)}
          />
        </div>
      )}

      {/* Doctor Summary Report Modal */}
      {showDoctorReportModal && (
        <DoctorSummaryModal
          messages={messages.filter((m) => reportMessageIds.has(m.id) || m.role === 'user')}
          symptoms={symptoms}
          onClose={() => setShowDoctorReportModal(false)}
        />
      )}

      {/* Sample Cases Modal */}
      {showSampleCasesModal && (
        <SampleCasesDrawer
          sampleCases={SAMPLE_CASES}
          onSelectCase={handleSelectSampleCase}
          onClose={() => setShowSampleCasesModal(false)}
        />
      )}

      {/* Body Explorer Modal */}
      {showBodyExplorerModal && (
        <BodyExplorerModal
          onClose={() => setShowBodyExplorerModal(false)}
          onSelectSamplePrompt={(prompt) => {
            handleSendMessage(prompt);
          }}
        />
      )}
    </div>
  );
}
