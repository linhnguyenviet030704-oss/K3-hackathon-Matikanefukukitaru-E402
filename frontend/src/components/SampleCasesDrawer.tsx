import React from 'react';
import { SampleCase } from '../types';
import { Sparkles, X, ChevronRight, Image as ImageIcon, MapPin, Clock } from 'lucide-react';

interface SampleCasesDrawerProps {
  sampleCases: SampleCase[];
  onSelectCase: (sample: SampleCase) => void;
  onClose: () => void;
}

export const SampleCasesDrawer: React.FC<SampleCasesDrawerProps> = ({
  sampleCases,
  onSelectCase,
  onClose,
}) => {
  return (
    <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-md flex items-center justify-center p-4 overflow-y-auto">
      <div className="bg-white border border-slate-200 rounded-2xl w-full max-w-2xl max-h-[90vh] flex flex-col shadow-2xl text-slate-800">
        {/* Header */}
        <div className="p-4 sm:p-5 border-b border-slate-200 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-teal-600 to-emerald-500 text-white flex items-center justify-center font-bold shadow-xs">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-bold text-slate-900">Sample Dermatology Cases</h2>
              <p className="text-xs text-slate-500 font-medium">Select a pre-loaded clinical case to test image analysis & AI responses</p>
            </div>
          </div>
          <button onClick={onClose} className="p-2 text-slate-400 hover:text-slate-700 rounded-lg">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Case List */}
        <div className="flex-1 overflow-y-auto p-5 space-y-3">
          {sampleCases.map((item) => (
            <div
              key={item.id}
              onClick={() => onSelectCase(item)}
              className="group bg-slate-50 hover:bg-white border border-slate-200 hover:border-teal-400 p-4 rounded-xl cursor-pointer transition-all flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between shadow-xs hover:shadow-md"
            >
              <div className="flex items-center gap-3">
                <img
                  src={item.imageUrl}
                  alt={item.title}
                  className="w-16 h-16 object-cover rounded-xl border border-slate-200 shrink-0 group-hover:scale-105 transition-transform"
                />
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] uppercase font-bold text-teal-800 bg-teal-100 border border-teal-300 px-2 py-0.5 rounded">
                      {item.category}
                    </span>
                  </div>
                  <h3 className="text-sm font-bold text-slate-900 group-hover:text-teal-700 transition-colors">
                    {item.title}
                  </h3>
                  <p className="text-xs text-slate-600 line-clamp-2">{item.description}</p>
                  <div className="flex items-center gap-3 text-[11px] text-slate-500 pt-1 font-medium">
                    <span className="flex items-center gap-1">
                      <MapPin className="w-3 h-3 text-teal-600" /> {item.symptoms.location}
                    </span>
                    <span className="flex items-center gap-1">
                      <Clock className="w-3 h-3 text-teal-600" /> {item.symptoms.duration}
                    </span>
                  </div>
                </div>
              </div>

              <button className="w-full sm:w-auto px-4 py-2 rounded-lg bg-teal-600 hover:bg-teal-700 text-white font-semibold text-xs flex items-center justify-center gap-1 shadow-xs shrink-0">
                <span>Run Case Analysis</span>
                <ChevronRight className="w-3.5 h-3.5" />
              </button>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
