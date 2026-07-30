import React, { useState } from 'react';
import { Eye, X, BookOpen, ChevronRight, ShieldCheck, Info } from 'lucide-react';

interface BodyExplorerModalProps {
  onClose: () => void;
  onSelectSamplePrompt: (promptText: string) => void;
}

export const BodyExplorerModal: React.FC<BodyExplorerModalProps> = ({
  onClose,
  onSelectSamplePrompt,
}) => {
  const [selectedZone, setSelectedZone] = useState<'face' | 'scalp' | 'arms' | 'torso' | 'legs'>('face');

  const zoneData = {
    face: {
      title: 'Facial Skin Conditions',
      description: 'The face contains high sebaceous gland density and delicate barrier skin easily reactive to environment, cosmetics, and hormonal shifts.',
      conditions: [
        {
          name: 'Acne Vulgaris / Papules',
          symptoms: 'Inflamed red bumps, pustules, or closed comedones around T-zone, cheeks, or jawline.',
          care: 'Use gentle non-comedogenic cleanser; consider topical salicylic acid or benzoyl peroxide; avoid picking.',
          prompt: 'I have inflamed breakouts on my face. How can I manage these without damaging my skin barrier?',
        },
        {
          name: 'Contact Dermatitis (Cosmetic Reaction)',
          symptoms: 'Sudden pink/red patch, stinging, tightness, or scaling after trying new products.',
          care: 'Pause all active serums/acids immediately; apply plain petrolatum or gentle barrier cream.',
          prompt: 'My face reacted with redness and stinging after applying a product. What is the skin barrier recovery protocol?',
        },
        {
          name: 'Rosacea Erythema',
          symptoms: 'Persistent central facial flushing, visible small capillaries, sensitivity to heat or spicy foods.',
          care: 'Daily broad-spectrum mineral sunscreen; avoid hot showers and triggers; consult dermatologist.',
          prompt: 'I experience persistent facial flushing and redness on my cheeks. What are the common triggers and care steps?',
        },
      ],
    },
    scalp: {
      title: 'Scalp & Neck Region',
      description: 'Scalp skin is prone to seborrheic yeast buildup, follicle inflammation, and sun exposure.',
      conditions: [
        {
          name: 'Seborrheic Dermatitis (Dandruff / Scalp Flaking)',
          symptoms: 'Greasy yellow or white flaking, itchy scalp, mild redness along hairline.',
          care: 'Use anti-fungal shampoo containing zinc pyrithione, ketoconazole, or selenium sulfide.',
          prompt: 'What causes persistent greasy scalp flaking and itchiness, and how do medicated shampoos work?',
        },
        {
          name: 'Folliculitis',
          symptoms: 'Small itchy or painful red pimple-like bumps around hair follicles on scalp or back of neck.',
          care: 'Avoid tight headwear; use antibacterial body wash or warm compresses; do not squeeze.',
          prompt: 'I have small itchy bumps around my hair follicles. What is folliculitis and how is it managed?',
        },
      ],
    },
    arms: {
      title: 'Arms & Elbow Flexures',
      description: 'Extensor surfaces (elbows) and flexural folds (inner elbow) react differently to autoimmune or dry skin conditions.',
      conditions: [
        {
          name: 'Flexural Eczema (Atopic Dermatitis)',
          symptoms: 'Dry, intensely itchy red patches in the inner elbow crease.',
          care: 'Apply thick ointment immediately after bathing; avoid scratch-itch cycles.',
          prompt: 'I have itchy dry patches in the bends of my inner elbows. How can I hydrate and soothe flexural eczema?',
        },
        {
          name: 'Psoriasis Plaques (Extensor)',
          symptoms: 'Thick raised red plaques with silvery white scale on outer elbows.',
          care: 'Keep skin moisturized with salicylic or lactic acid lotions; seek dermatological evaluation.',
          prompt: 'What distinguishes psoriasis plaques on elbows from standard dry skin?',
        },
      ],
    },
    torso: {
      title: 'Chest, Back & Abdomen',
      description: 'Large surface area subject to clothing friction, sweat entrapment, and pigmented mole monitoring.',
      conditions: [
        {
          name: 'Pigmented Nevi (Moles)',
          symptoms: 'Flat or raised brown/tan spots. Routine checks monitor the ABCDE criteria.',
          care: 'Annual dermatologist skin check; monthly self-examination for changing borders or colors.',
          prompt: 'What are the ABCDE rules for evaluating moles on the back and torso?',
        },
        {
          name: 'Pityriasis Versicolor (Tinea)',
          symptoms: 'Light pink or pale patches on upper chest/back that become more noticeable after sweating.',
          care: 'Over-the-counter antifungal cleansers or shampoos used as body wash.',
          prompt: 'I noticed lighter discolored spots on my chest after summer. Could this be tinea versicolor?',
        },
      ],
    },
    legs: {
      title: 'Legs, Knees & Feet',
      description: 'Lower extremities endure dry winter weather, razor bumps, and friction.',
      conditions: [
        {
          name: 'Xerosis (Severe Dry Skin / Asteatotic Dermatitis)',
          symptoms: 'Fissured, cracked, faint "crazy-paving" pattern on shins, intensely dry.',
          care: 'Thick ceramide creams; shorten warm shower duration; avoid harsh sulfates.',
          prompt: 'My shins look cracked like dry riverbed clay in winter. How do ceramide creams rebuild barrier lipid layers?',
        },
      ],
    },
  };

  const current = zoneData[selectedZone];

  return (
    <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-md flex items-center justify-center p-4 overflow-y-auto">
      <div className="bg-white border border-slate-200 rounded-2xl w-full max-w-3xl flex flex-col shadow-2xl text-slate-800">
        {/* Header */}
        <div className="p-4 sm:p-5 border-b border-slate-200 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-teal-100 text-teal-700 flex items-center justify-center">
              <Eye className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-bold text-slate-900">Interactive Skin Zone Map</h2>
              <p className="text-xs text-slate-500 font-medium">Educational reference guide on regional skin characteristics</p>
            </div>
          </div>
          <button onClick={onClose} className="p-2 text-slate-400 hover:text-slate-700 rounded-lg">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Zone Tabs */}
        <div className="p-3 border-b border-slate-200 bg-slate-50 flex items-center gap-1.5 overflow-x-auto text-xs">
          {(['face', 'scalp', 'arms', 'torso', 'legs'] as const).map((z) => (
            <button
              key={z}
              onClick={() => setSelectedZone(z)}
              className={`px-3.5 py-2 rounded-xl capitalize font-semibold transition-all shrink-0 ${
                selectedZone === z
                  ? 'bg-teal-600 text-white shadow-sm'
                  : 'bg-white border border-slate-200 text-slate-700 hover:bg-slate-100'
              }`}
            >
              {z === 'face' ? 'Face & Chin' : z === 'scalp' ? 'Scalp & Neck' : z === 'arms' ? 'Arms & Elbows' : z === 'torso' ? 'Chest & Back' : 'Legs & Feet'}
            </button>
          ))}
        </div>

        {/* Content Body */}
        <div className="p-5 space-y-4 text-xs">
          <div className="bg-slate-50 p-3.5 rounded-xl border border-slate-200 space-y-1">
            <h3 className="font-bold text-teal-800 text-sm">{current.title}</h3>
            <p className="text-slate-700 leading-relaxed text-[11px] font-normal">{current.description}</p>
          </div>

          <div className="space-y-3">
            <h4 className="font-bold text-slate-900 text-xs uppercase tracking-wider flex items-center gap-1">
              <BookOpen className="w-3.5 h-3.5 text-teal-600" />
              Common Regional Conditions
            </h4>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {current.conditions.map((cond, idx) => (
                <div
                  key={idx}
                  className="bg-white p-4 rounded-xl border border-slate-200 hover:border-teal-400 transition-all space-y-2 flex flex-col justify-between shadow-2xs"
                >
                  <div className="space-y-1.5">
                    <h5 className="font-bold text-slate-900 text-xs flex items-center justify-between">
                      <span>{cond.name}</span>
                      <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
                    </h5>
                    <p className="text-[11px] text-slate-700 leading-relaxed">
                      <strong className="text-slate-900">Characteristics:</strong> {cond.symptoms}
                    </p>
                    <p className="text-[11px] text-teal-900 leading-relaxed bg-teal-50 p-2 rounded-lg border border-teal-200">
                      <strong className="text-teal-900">Barrier Care:</strong> {cond.care}
                    </p>
                  </div>

                  <button
                    onClick={() => {
                      onSelectSamplePrompt(cond.prompt);
                      onClose();
                    }}
                    className="w-full mt-2 py-1.5 px-3 rounded-lg bg-teal-50 hover:bg-teal-600 text-teal-800 hover:text-white font-bold text-[11px] transition-all flex items-center justify-center gap-1 border border-teal-200"
                  >
                    <span>Ask AI About This Condition</span>
                    <ChevronRight className="w-3 h-3" />
                  </button>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-slate-200 bg-slate-50 text-[11px] text-slate-500 flex items-center gap-2 rounded-b-2xl font-medium">
          <Info className="w-4 h-4 text-teal-600 shrink-0" />
          <span>This interactive zone guide serves as general health education. Consult a dermatologist for personal skin evaluations.</span>
        </div>
      </div>
    </div>
  );
};
