import React, { useState } from 'react';
import { Citation } from '../types';
import { BookOpen, ExternalLink, ShieldCheck, Search, Filter, Bookmark, Info, PanelRightClose, X } from 'lucide-react';

interface CitationsSidebarProps {
  citations: Citation[];
  selectedCitation: Citation | null;
  onClearSelectedCitation: () => void;
  isOpen: boolean;
  onToggleOpen: () => void;
}

export const CitationsSidebar: React.FC<CitationsSidebarProps> = ({
  citations,
  selectedCitation,
  onClearSelectedCitation,
  isOpen,
  onToggleOpen,
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [filterCategory, setFilterCategory] = useState<string>('all');

  const filteredCitations = citations.filter((c) => {
    const matchesSearch =
      c.source.toLowerCase().includes(searchTerm.toLowerCase()) ||
      c.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      c.summary.toLowerCase().includes(searchTerm.toLowerCase());

    const matchesCategory = filterCategory === 'all' || c.category === filterCategory;

    return matchesSearch && matchesCategory;
  });

  if (!isOpen) return null;

  return (
    <>
      {/* Mobile Overlay Backdrop */}
      <div
        className="lg:hidden fixed inset-0 bg-slate-900/50 backdrop-blur-xs z-40"
        onClick={onToggleOpen}
      />

      {/* Sidebar Container - Right Edge */}
      <aside
        className="fixed lg:static inset-y-0 right-0 z-40 w-72 sm:w-80 bg-slate-50 border-l border-slate-200 flex flex-col h-full min-h-0 shrink-0 shadow-xl lg:shadow-none transition-all duration-300 ease-in-out"
      >
        {/* Sidebar Header */}
        <div className="p-4 border-b border-slate-200 bg-white flex items-center justify-between gap-2 shrink-0">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-teal-100 text-teal-700 flex items-center justify-center font-semibold">
              <BookOpen className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-sm font-bold text-slate-900 leading-none">Tài Liệu Y Khoa</h2>
              <p className="text-[11px] text-slate-500 font-medium mt-0.5">Source Citations & Guidelines</p>
            </div>
          </div>

          <button
            onClick={onToggleOpen}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-200/60 transition-colors"
            title="Đóng sidebar tài liệu"
          >
            <PanelRightClose className="w-4 h-4 hidden lg:block" />
            <X className="w-4 h-4 lg:hidden" />
          </button>
        </div>


      {/* Selected Highlight Banner if clicked from a message */}
      {selectedCitation && (
        <div className="bg-teal-50 p-3 border-b border-teal-200 text-xs shrink-0">
          <div className="flex items-center justify-between font-bold text-teal-900 mb-1">
            <span className="flex items-center gap-1">
              <Bookmark className="w-3.5 h-3.5 text-teal-600" />
              Highlighted Reference
            </span>
            <button
              onClick={onClearSelectedCitation}
              className="text-[10px] text-teal-700 hover:text-teal-950 underline font-medium"
            >
              Clear Focus
            </button>
          </div>
          <p className="text-slate-800 font-semibold">{selectedCitation.title}</p>
          <p className="text-[11px] text-slate-600 mt-0.5">{selectedCitation.source}</p>
        </div>
      )}

      {/* Search & Category Filter */}
      <div className="p-3 border-b border-slate-200 bg-white space-y-2 shrink-0">
        <div className="relative">
          <Search className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-2.5" />
          <input
            type="text"
            placeholder="Search guidelines or sources..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full bg-slate-50 border border-slate-200 rounded-lg pl-8 pr-3 py-1.5 text-xs text-slate-800 placeholder-slate-400 focus:outline-none focus:border-teal-500 focus:bg-white transition-all"
          />
        </div>

        <div className="flex items-center gap-1.5 overflow-x-auto pb-1 text-[11px]">
          <span className="text-slate-500 text-[10px] shrink-0 flex items-center gap-1">
            <Filter className="w-2.5 h-2.5" /> Filter:
          </span>
          {['all', 'Guideline', 'Peer-Reviewed Study', 'Clinical Reference'].map((cat) => (
            <button
              key={cat}
              onClick={() => setFilterCategory(cat)}
              className={`px-2 py-0.5 rounded-md shrink-0 transition-colors text-[11px] font-medium ${
                filterCategory === cat
                  ? 'bg-teal-100 text-teal-800 border border-teal-300 font-semibold'
                  : 'bg-slate-100 text-slate-600 hover:text-slate-900'
              }`}
            >
              {cat === 'all' ? 'All Sources' : cat}
            </button>
          ))}
        </div>
      </div>

      {/* Citations List */}
      <div className="flex-1 overflow-y-auto min-h-0 p-3 space-y-3">
        {filteredCitations.length === 0 ? (
          <div className="p-6 text-center text-slate-500 text-xs">
            No citation records match your search query.
          </div>
        ) : (
          filteredCitations.map((cit) => {
            const isHighlighted = selectedCitation?.id === cit.id;

            return (
              <div
                key={cit.id}
                className={`p-3.5 rounded-xl border transition-all text-xs space-y-2 shadow-xs ${
                  isHighlighted
                    ? 'bg-teal-50/90 border-teal-500 ring-2 ring-teal-200'
                    : 'bg-white hover:border-slate-300 border-slate-200'
                }`}
              >
                <div className="flex items-start justify-between gap-1">
                  <span className="inline-block px-2 py-0.5 rounded text-[10px] font-semibold bg-slate-100 text-teal-800 border border-slate-200">
                    {cit.category}
                  </span>
                  <span className="text-[10px] text-slate-500 font-semibold flex items-center gap-1">
                    <ShieldCheck className="w-3 h-3 text-emerald-600" />
                    {cit.evidenceLevel}
                  </span>
                </div>

                <div>
                  <h3 className="font-bold text-slate-900 leading-snug">{cit.title}</h3>
                  <div className="text-[11px] font-semibold text-teal-700 mt-0.5">
                    {cit.source} {cit.year ? `(${cit.year})` : ''}
                  </div>
                </div>

                <p className="text-[11px] text-slate-700 leading-relaxed bg-slate-50 p-2.5 rounded-lg border border-slate-200/80">
                  {cit.summary}
                </p>

                {cit.url && (
                  <a
                    href={cit.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1 text-[11px] text-teal-700 hover:text-teal-900 hover:underline pt-1 font-semibold"
                  >
                    <span>Read Full Guideline / Reference</span>
                    <ExternalLink className="w-3 h-3" />
                  </a>
                )}
              </div>
            );
          })
        )}
      </div>

      {/* Footer Info */}
      <div className="p-3 border-t border-slate-200 bg-white text-[10px] text-slate-500 flex items-center gap-2 shrink-0">
        <Info className="w-3.5 h-3.5 text-teal-600 shrink-0" />
        <span>Citations automatically linked based on response topics.</span>
      </div>
    </aside>
    </>
  );
};

