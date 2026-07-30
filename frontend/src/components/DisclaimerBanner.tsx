import React, { useState } from 'react';
import { AlertTriangle, ShieldCheck, ChevronDown, ChevronUp, AlertCircle, PhoneCall } from 'lucide-react';

export const DisclaimerBanner: React.FC = () => {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <div className="bg-amber-50/80 border-b border-amber-200/80 text-slate-800 text-xs px-4 py-2.5 transition-all shrink-0">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-start md:items-center justify-between gap-2">
        <div className="flex items-center gap-2.5 flex-1">
          <div className="w-5 h-5 rounded-full bg-amber-100 text-amber-700 flex items-center justify-center shrink-0">
            <ShieldCheck className="w-3.5 h-3.5" />
          </div>
          <div>
            <span className="font-bold text-amber-900 mr-1.5">Educational Medical Information:</span>
            <span className="text-slate-700">
              DermaCare AI provides evidence-backed dermatological information and photo observations. It is not a clinical diagnostic tool and cannot replace a board-certified doctor.
            </span>
          </div>
        </div>

        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="flex items-center gap-1 text-amber-800 hover:text-amber-950 font-semibold shrink-0 text-[11px] bg-amber-100/80 hover:bg-amber-200/80 px-2.5 py-1 rounded-md transition-all"
        >
          <span>{isExpanded ? 'Hide Red Flags & Guidance' : 'When to Seek Urgent Care?'}</span>
          {isExpanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
        </button>
      </div>

      {isExpanded && (
        <div className="max-w-7xl mx-auto mt-3 pt-3 border-t border-amber-200 grid grid-cols-1 md:grid-cols-3 gap-3 text-slate-700 text-xs">
          <div className="bg-white p-3 rounded-xl border border-amber-200 shadow-xs">
            <div className="font-bold text-amber-800 flex items-center gap-1.5 mb-1">
              <AlertTriangle className="w-4 h-4 text-amber-600" />
              Immediate Red Flags
            </div>
            <p className="text-[11px] text-slate-600 leading-relaxed">
              If your skin lesion is rapidly expanding, oozing pus, accompanied by a severe fever, chills, intense pain, or lip/eye swelling, seek immediate emergency care.
            </p>
          </div>

          <div className="bg-white p-3 rounded-xl border border-teal-200 shadow-xs">
            <div className="font-bold text-teal-800 flex items-center gap-1.5 mb-1">
              <ShieldCheck className="w-4 h-4 text-teal-600" />
              ABCDE Mole Safety Standard
            </div>
            <p className="text-[11px] text-slate-600 leading-relaxed">
              Watch for Asymmetry, Irregular Borders, Color variations (black/red/blue), Diameter over 6mm, or Evolving size/shape.
            </p>
          </div>

          <div className="bg-white p-3 rounded-xl border border-rose-200 shadow-xs">
            <div className="font-bold text-rose-800 flex items-center gap-1.5 mb-1">
              <PhoneCall className="w-4 h-4 text-rose-600" />
              Emergency Services
            </div>
            <p className="text-[11px] text-slate-600 leading-relaxed">
              For severe allergic reactions, difficulty breathing, or widespread hives with dizziness, call emergency services (911/112) immediately.
            </p>
          </div>
        </div>
      )}
    </div>
  );
};
