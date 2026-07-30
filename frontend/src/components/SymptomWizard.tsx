import React from 'react';
import { SymptomFilter } from '../types';
import { Sliders, X, Check, Activity, MapPin, Clock } from 'lucide-react';

interface SymptomWizardProps {
  symptoms: SymptomFilter;
  setSymptoms: React.Dispatch<React.SetStateAction<SymptomFilter>>;
  onClose: () => void;
  onApply: () => void;
}

export const SymptomWizard: React.FC<SymptomWizardProps> = ({
  symptoms,
  setSymptoms,
  onClose,
  onApply,
}) => {
  const bodyLocations = [
    'Face / Cheek / Chin',
    'Scalp / Neck',
    'Arms / Forearm / Elbows',
    'Chest / Back / Torso',
    'Hands / Fingers',
    'Legs / Knees / Feet',
  ];

  const durations = [
    'Less than 24 hours',
    '1 to 3 days',
    '1 to 2 weeks',
    '1 month or longer',
    'Recurring over months',
  ];

  return (
    <div className="bg-white border border-slate-200 rounded-2xl p-4 sm:p-5 shadow-2xl space-y-4 max-w-lg w-full text-slate-800">
      <div className="flex items-center justify-between border-b border-slate-200 pb-3">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-teal-100 text-teal-700 flex items-center justify-center">
            <Sliders className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-slate-900">Symptom Details Wizard</h3>
            <p className="text-[11px] text-slate-500 font-medium">Provide optional context for better response accuracy</p>
          </div>
        </div>
        <button onClick={onClose} className="p-1 text-slate-400 hover:text-slate-700 rounded-lg">
          <X className="w-4 h-4" />
        </button>
      </div>

      <div className="space-y-3.5 text-xs">
        {/* Body Location */}
        <div>
          <label className="font-bold text-slate-800 flex items-center gap-1.5 mb-1.5">
            <MapPin className="w-3.5 h-3.5 text-teal-600" />
            Affected Body Area
          </label>
          <div className="grid grid-cols-2 gap-1.5">
            {bodyLocations.map((loc) => (
              <button
                key={loc}
                type="button"
                onClick={() => setSymptoms((s) => ({ ...s, location: loc }))}
                className={`p-2 rounded-lg text-left transition-all border ${
                  symptoms.location === loc
                    ? 'bg-teal-50 border-teal-500 text-teal-900 font-bold'
                    : 'bg-slate-50 border-slate-200 text-slate-700 hover:bg-slate-100'
                }`}
              >
                {loc}
              </button>
            ))}
          </div>
        </div>

        {/* Duration */}
        <div>
          <label className="font-bold text-slate-800 flex items-center gap-1.5 mb-1.5">
            <Clock className="w-3.5 h-3.5 text-teal-600" />
            Symptom Duration
          </label>
          <select
            value={symptoms.duration}
            onChange={(e) => setSymptoms((s) => ({ ...s, duration: e.target.value }))}
            className="w-full bg-slate-50 border border-slate-200 rounded-lg p-2 text-slate-800 focus:outline-none focus:border-teal-500"
          >
            {durations.map((d) => (
              <option key={d} value={d}>
                {d}
              </option>
            ))}
          </select>
        </div>

        {/* Sliders: Itch & Pain */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-1">
          <div className="bg-slate-50 p-3 rounded-xl border border-slate-200">
            <div className="flex justify-between items-center mb-1 font-semibold text-slate-800">
              <span>Itch Severity</span>
              <span className="text-amber-700 font-bold">{symptoms.itchLevel}/10</span>
            </div>
            <input
              type="range"
              min="0"
              max="10"
              value={symptoms.itchLevel}
              onChange={(e) => setSymptoms((s) => ({ ...s, itchLevel: Number(e.target.value) }))}
              className="w-full accent-amber-600 cursor-pointer h-1.5 bg-slate-200 rounded-lg"
            />
          </div>

          <div className="bg-slate-50 p-3 rounded-xl border border-slate-200">
            <div className="flex justify-between items-center mb-1 font-semibold text-slate-800">
              <span>Pain / Stinging</span>
              <span className="text-rose-700 font-bold">{symptoms.painLevel}/10</span>
            </div>
            <input
              type="range"
              min="0"
              max="10"
              value={symptoms.painLevel}
              onChange={(e) => setSymptoms((s) => ({ ...s, painLevel: Number(e.target.value) }))}
              className="w-full accent-rose-600 cursor-pointer h-1.5 bg-slate-200 rounded-lg"
            />
          </div>
        </div>

        {/* Spreading Toggle */}
        <div className="flex items-center justify-between bg-slate-50 p-3 rounded-xl border border-slate-200">
          <div className="flex items-center gap-2">
            <Activity className="w-4 h-4 text-teal-600" />
            <span className="font-semibold text-slate-800">Is the rash / spot expanding or spreading?</span>
          </div>
          <button
            type="button"
            onClick={() => setSymptoms((s) => ({ ...s, isSpreading: !s.isSpreading }))}
            className={`w-12 h-6 rounded-full transition-colors relative p-0.5 ${
              symptoms.isSpreading ? 'bg-teal-600' : 'bg-slate-300'
            }`}
          >
            <div
              className={`w-5 h-5 rounded-full bg-white transition-transform ${
                symptoms.isSpreading ? 'translate-x-6' : 'translate-x-0'
              }`}
            />
          </button>
        </div>
      </div>

      <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-200">
        <button
          onClick={onClose}
          className="px-3 py-1.5 rounded-lg text-xs font-semibold text-slate-500 hover:text-slate-800"
        >
          Cancel
        </button>
        <button
          onClick={onApply}
          className="px-4 py-1.5 rounded-lg text-xs font-bold bg-teal-600 hover:bg-teal-700 text-white flex items-center gap-1.5 shadow-sm"
        >
          <Check className="w-3.5 h-3.5" />
          Attach Symptom Context
        </button>
      </div>
    </div>
  );
};
