import React, { useRef, useState } from 'react';
import { ChatMessage, SymptomFilter } from '../types';
import { FileText, Printer, Download, Check, X, Stethoscope, AlertCircle, Copy } from 'lucide-react';

interface DoctorSummaryModalProps {
  messages: ChatMessage[];
  symptoms: SymptomFilter;
  onClose: () => void;
}

export const DoctorSummaryModal: React.FC<DoctorSummaryModalProps> = ({
  messages,
  symptoms,
  onClose,
}) => {
  const [copied, setCopied] = useState(false);
  const printRef = useRef<HTMLDivElement>(null);

  // Extract messages saved or key messages
  const userMessages = messages.filter((m) => m.role === 'user');
  const aiMessages = messages.filter((m) => m.role === 'assistant');
  const uploadedImages = messages.map((m) => m.image).filter(Boolean);

  const handlePrint = () => {
    window.print();
  };

  const handleCopySummary = () => {
    let summaryText = `DERMACARE AI - PRE-CONSULTATION DERMATOLOGY SUMMARY REPORT\nDate: ${new Date().toLocaleDateString()}\n\n`;

    summaryText += `PATIENT REPORTED SYMPTOMS:\n`;
    if (symptoms.location) summaryText += `- Location: ${symptoms.location}\n`;
    if (symptoms.duration) summaryText += `- Duration: ${symptoms.duration}\n`;
    summaryText += `- Itching Level: ${symptoms.itchLevel}/10\n`;
    summaryText += `- Pain Level: ${symptoms.painLevel}/10\n`;
    summaryText += `- Spreading Status: ${symptoms.isSpreading ? 'Yes' : 'No'}\n\n`;

    summaryText += `KEY USER INQUIRIES:\n`;
    userMessages.forEach((m, idx) => {
      summaryText += `${idx + 1}. ${m.content}\n`;
    });

    summaryText += `\nAI EDUCATIONAL OBSERVATIONS:\n`;
    aiMessages.forEach((m, idx) => {
      summaryText += `${idx + 1}. ${m.content.slice(0, 300)}...\n`;
    });

    summaryText += `\nQUESTIONS TO ASK THE DERMATOLOGIST:\n`;
    summaryText += `- What is the likely cause of my skin condition?\n`;
    summaryText += `- Are there specific triggers I should avoid in my routine?\n`;
    summaryText += `- Do I need prescription topical therapy or diagnostic patch testing?\n`;
    summaryText += `\n*Note: This report is generated as an educational tool to aid communication with your healthcare provider.*`;

    navigator.clipboard.writeText(summaryText);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-md flex items-center justify-center p-4 overflow-y-auto">
      <div className="bg-white border border-slate-200 rounded-2xl w-full max-w-2xl max-h-[90vh] flex flex-col shadow-2xl text-slate-800">
        {/* Modal Header */}
        <div className="p-4 sm:p-5 border-b border-slate-200 flex items-center justify-between bg-white rounded-t-2xl">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-emerald-100 text-emerald-800 flex items-center justify-center">
              <FileText className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-bold text-slate-900">Doctor Visit Summary Report</h2>
              <p className="text-xs text-slate-500 font-medium">Exportable preparation sheet for your dermatologist appointment</p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={handleCopySummary}
              className="p-2 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs flex items-center gap-1.5 transition-colors font-semibold"
              title="Copy Summary Text"
            >
              {copied ? <Check className="w-4 h-4 text-emerald-600" /> : <Copy className="w-4 h-4" />}
              <span className="hidden sm:inline">{copied ? 'Copied' : 'Copy'}</span>
            </button>

            <button
              onClick={handlePrint}
              className="p-2 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white text-xs flex items-center gap-1.5 transition-colors font-semibold shadow-xs"
              title="Print or Save PDF"
            >
              <Printer className="w-4 h-4" />
              <span className="hidden sm:inline">Print / PDF</span>
            </button>

            <button onClick={onClose} className="p-2 text-slate-400 hover:text-slate-700 rounded-lg">
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Printable Report Document View */}
        <div className="flex-1 overflow-y-auto p-5 space-y-5 text-slate-800 text-xs" ref={printRef}>
          {/* Document Header */}
          <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 flex items-center justify-between">
            <div className="space-y-1">
              <div className="text-sm font-bold text-teal-800 flex items-center gap-2">
                <Stethoscope className="w-4 h-4 text-teal-600" />
                DermaCare AI Consultation Brief
              </div>
              <p className="text-slate-500 text-[11px] font-medium">Prepared for Clinical Consultation</p>
            </div>
            <div className="text-right text-[11px] text-slate-500 font-medium">
              <div>Date: {new Date().toLocaleDateString()}</div>
              <div>Status: Patient Self-Report</div>
            </div>
          </div>

          {/* Section 1: Patient Symptoms */}
          <div className="space-y-2">
            <h3 className="font-bold text-teal-800 text-xs uppercase tracking-wider flex items-center gap-1.5">
              1. Patient Reported Symptoms
            </h3>
            <div className="bg-slate-50 p-3.5 rounded-xl border border-slate-200 grid grid-cols-2 sm:grid-cols-4 gap-3 text-slate-800">
              <div>
                <span className="text-[10px] text-slate-500 block font-medium">Affected Area</span>
                <span className="font-bold text-slate-900">{symptoms.location || 'Not specified'}</span>
              </div>
              <div>
                <span className="text-[10px] text-slate-500 block font-medium">Duration</span>
                <span className="font-bold text-slate-900">{symptoms.duration || 'Not specified'}</span>
              </div>
              <div>
                <span className="text-[10px] text-slate-500 block font-medium">Itch Severity</span>
                <span className="font-bold text-amber-700">{symptoms.itchLevel}/10</span>
              </div>
              <div>
                <span className="text-[10px] text-slate-500 block font-medium">Spreading</span>
                <span className="font-bold text-slate-900">{symptoms.isSpreading ? 'Yes' : 'No'}</span>
              </div>
            </div>
          </div>

          {/* Section 2: Uploaded Photos */}
          {uploadedImages.length > 0 && (
            <div className="space-y-2">
              <h3 className="font-bold text-teal-800 text-xs uppercase tracking-wider">
                2. Uploaded Lesion Photographs
              </h3>
              <div className="flex flex-wrap gap-2">
                {uploadedImages.map((img, idx) => (
                  img && (
                    <div key={idx} className="relative rounded-lg overflow-hidden border border-slate-200 bg-slate-50 p-1">
                      <img src={img.url} alt="Lesion photo" className="h-24 w-24 object-cover rounded" />
                    </div>
                  )
                ))}
              </div>
            </div>
          )}

          {/* Section 3: Conversation Log & Educational Summaries */}
          <div className="space-y-2">
            <h3 className="font-bold text-teal-800 text-xs uppercase tracking-wider">
              3. Patient Inquiries & AI Educational Notes
            </h3>
            <div className="space-y-3">
              {messages.length === 0 ? (
                <p className="text-slate-400 italic">No chat history recorded yet.</p>
              ) : (
                messages.map((m) => (
                  <div
                    key={m.id}
                    className={`p-3 rounded-xl border ${
                      m.role === 'assistant'
                        ? 'bg-slate-50 border-slate-200'
                        : 'bg-teal-50/80 border-teal-200'
                    }`}
                  >
                    <div className="font-bold text-slate-800 mb-1">
                      {m.role === 'assistant' ? 'AI Observation Note:' : 'Patient Question:'}
                    </div>
                    <div className="text-slate-800 leading-relaxed">{m.content}</div>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Section 4: Suggested Questions for Doctor */}
          <div className="bg-emerald-50/80 p-4 rounded-xl border border-emerald-200 space-y-2">
            <h3 className="font-bold text-emerald-900 text-xs flex items-center gap-1.5">
              <Check className="w-4 h-4 text-emerald-600" />
              Suggested Questions for Your Dermatologist
            </h3>
            <ul className="list-disc list-inside space-y-1 text-slate-700 text-xs">
              <li>What is the formal diagnosis for my current skin symptoms?</li>
              <li>Are there barrier-restoring cleansers or ointments suitable for my skin type?</li>
              <li>Should I stop using any of my current skincare products or soaps?</li>
              <li>Under what specific changes or red flags should I return for follow-up care?</li>
            </ul>
          </div>

          <div className="text-[10px] text-slate-500 border-t border-slate-200 pt-3 flex items-center gap-1.5">
            <AlertCircle className="w-3.5 h-3.5 shrink-0 text-slate-400" />
            <span>This summary report is generated solely to assist patient-physician dialogue. It is not a diagnostic record.</span>
          </div>
        </div>
      </div>
    </div>
  );
};
