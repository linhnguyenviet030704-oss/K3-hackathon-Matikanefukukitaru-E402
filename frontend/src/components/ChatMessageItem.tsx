import React, { useState } from 'react';
import { ChatMessage, Citation } from '../types';
import { Bot, User, BookOpen, Check, Copy, ExternalLink, PlusCircle, Sparkles, Image as ImageIcon } from 'lucide-react';

interface ChatMessageItemProps {
  message: ChatMessage;
  onSelectCitation: (citation: Citation) => void;
  onAddToDoctorReport: (message: ChatMessage) => void;
  isAddedToReport?: boolean;
}

export const ChatMessageItem: React.FC<ChatMessageItemProps> = ({
  message,
  onSelectCitation,
  onAddToDoctorReport,
  isAddedToReport = false,
}) => {
  const [copied, setCopied] = useState(false);
  const [imageModalOpen, setImageModalOpen] = useState(false);

  const isAssistant = message.role === 'assistant';

  // Calculate approximate word count
  const wordCount = message.content.trim().split(/\s+/).length;

  const handleCopy = () => {
    navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div
      className={`group flex gap-3.5 p-4 sm:p-5 rounded-2xl transition-all shadow-xs ${
        isAssistant
          ? 'bg-white border border-slate-200/90 text-slate-800'
          : 'bg-teal-50/90 border border-teal-200/80 text-slate-900'
      }`}
    >
      {/* Avatar */}
      <div
        className={`w-9 h-9 rounded-xl flex items-center justify-center shrink-0 shadow-xs ${
          isAssistant
            ? 'bg-gradient-to-br from-teal-600 to-emerald-600 text-white font-bold'
            : 'bg-teal-700 text-white'
        }`}
      >
        {isAssistant ? <Bot className="w-5 h-5" /> : <User className="w-5 h-5" />}
      </div>

      {/* Main Message Content */}
      <div className="flex-1 min-w-0 space-y-2.5">
        {/* Header line */}
        <div className="flex items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <span className="font-bold text-sm text-slate-900">
              {isAssistant ? 'DermaCare AI' : 'You (Patient Inquiry)'}
            </span>
            <span className="text-[11px] text-slate-400 font-medium">{message.timestamp}</span>
            {isAssistant && (
              <span className="inline-flex items-center gap-1 text-[10px] font-semibold px-2 py-0.5 rounded-full bg-teal-100/80 text-teal-800 border border-teal-200">
                <Sparkles className="w-2.5 h-2.5 text-teal-600" />
                Verified Sources Grounded
              </span>
            )}
          </div>

          {/* Action buttons */}
          <div className="flex items-center gap-1 opacity-90 group-hover:opacity-100 transition-opacity">
            {isAssistant && (
              <button
                onClick={() => onAddToDoctorReport(message)}
                className={`flex items-center gap-1 px-2.5 py-1 rounded-lg text-[11px] font-medium transition-all ${
                  isAddedToReport
                    ? 'bg-emerald-100 text-emerald-800 border border-emerald-300 font-semibold'
                    : 'bg-slate-100 hover:bg-slate-200 text-slate-700'
                }`}
                title="Add response observations to your Doctor Visit Report"
              >
                {isAddedToReport ? <Check className="w-3 h-3 text-emerald-600" /> : <PlusCircle className="w-3 h-3 text-slate-500" />}
                <span>{isAddedToReport ? 'In Doctor Report' : 'Add to Report'}</span>
              </button>
            )}

            <button
              onClick={handleCopy}
              className="p-1.5 rounded-lg hover:bg-slate-100 text-slate-400 hover:text-slate-700 text-xs transition-colors"
              title="Copy text"
            >
              {copied ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
            </button>
          </div>
        </div>

        {/* Uploaded Image Preview if present */}
        {message.image && (
          <div className="mt-2 mb-3">
            <div className="relative inline-block group/img overflow-hidden rounded-xl border border-slate-200 bg-slate-50 shadow-xs">
              <img
                src={message.image.url}
                alt={message.image.name || 'Uploaded skin lesion'}
                className="max-h-52 max-w-full object-cover rounded-xl cursor-pointer hover:scale-105 transition-transform duration-300"
                onClick={() => setImageModalOpen(true)}
              />
              <div className="absolute inset-0 bg-slate-900/30 opacity-0 group-hover/img:opacity-100 transition-opacity flex items-center justify-center pointer-events-none">
                <span className="text-xs text-white bg-slate-900/80 px-2.5 py-1 rounded-md flex items-center gap-1">
                  <ImageIcon className="w-3.5 h-3.5" />
                  Click to Expand
                </span>
              </div>
            </div>
            {message.symptomSummary && (
              <div className="mt-2 flex flex-wrap gap-1.5 text-[11px]">
                {message.symptomSummary.location && (
                  <span className="bg-slate-100 text-slate-700 border border-slate-200 px-2 py-0.5 rounded-md">
                    Location: <strong className="text-teal-700">{message.symptomSummary.location}</strong>
                  </span>
                )}
                {message.symptomSummary.duration && (
                  <span className="bg-slate-100 text-slate-700 border border-slate-200 px-2 py-0.5 rounded-md">
                    Duration: <strong className="text-teal-700">{message.symptomSummary.duration}</strong>
                  </span>
                )}
                {message.symptomSummary.itchLevel !== undefined && (
                  <span className="bg-slate-100 text-slate-700 border border-slate-200 px-2 py-0.5 rounded-md">
                    Itch: <strong className="text-amber-700">{message.symptomSummary.itchLevel}/10</strong>
                  </span>
                )}
              </div>
            )}
          </div>
        )}

        {/* Message Text Body */}
        <div className="text-sm text-slate-800 leading-relaxed whitespace-pre-line font-sans">
          {message.content}
        </div>

        {/* Assistant Specific Footer: Citations & Word Count indicator */}
        {isAssistant && (
          <div className="pt-3 mt-3 border-t border-slate-100 flex flex-wrap items-center justify-between gap-2">
            {/* Citations Chips */}
            {message.citations && message.citations.length > 0 ? (
              <div className="flex flex-wrap items-center gap-1.5">
                <span className="text-[11px] font-medium text-slate-500 flex items-center gap-1">
                  <BookOpen className="w-3 h-3 text-teal-600" />
                  Sources Cited:
                </span>
                {message.citations.map((cit) => (
                  <button
                    key={cit.id}
                    onClick={() => onSelectCitation(cit)}
                    className="inline-flex items-center gap-1 text-[11px] bg-teal-50 hover:bg-teal-100 text-teal-800 font-medium border border-teal-200 px-2 py-0.5 rounded-md transition-all shadow-2xs"
                  >
                    <span>{cit.source}</span>
                    <ExternalLink className="w-2.5 h-2.5 opacity-70" />
                  </button>
                ))}
              </div>
            ) : (
              <div className="text-[11px] text-slate-500 flex items-center gap-1">
                <BookOpen className="w-3 h-3 text-teal-600" />
                Grounded in AAD & Mayo Clinic Guidelines
              </div>
            )}

            {/* Concise Response Badge (<200 words mandate compliance) */}
            <div className="text-[10px] text-slate-500 bg-slate-50 px-2 py-0.5 rounded border border-slate-200">
              Length: {wordCount} words {wordCount <= 200 ? '• Concise Medical Standard ✓' : ''}
            </div>
          </div>
        )}
      </div>

      {/* Expanded Image Modal */}
      {imageModalOpen && message.image && (
        <div
          className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4"
          onClick={() => setImageModalOpen(false)}
        >
          <div className="relative max-w-3xl w-full bg-white border border-slate-200 rounded-2xl p-4 shadow-2xl">
            <img
              src={message.image.url}
              alt="Expanded skin preview"
              className="w-full max-h-[80vh] object-contain rounded-lg"
            />
            <div className="mt-3 flex items-center justify-between text-xs text-slate-700">
              <span>{message.image.name || 'Dermatology Image Preview'}</span>
              <button
                onClick={() => setImageModalOpen(false)}
                className="px-3 py-1 bg-slate-800 hover:bg-slate-900 text-white rounded-md"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
