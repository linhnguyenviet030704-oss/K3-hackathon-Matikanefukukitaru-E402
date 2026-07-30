export interface Citation {
  id: string;
  source: string; // e.g., "American Academy of Dermatology (AAD)"
  title: string;
  year?: string;
  category: 'Guideline' | 'Peer-Reviewed Study' | 'Clinical Reference' | 'Educational Resource';
  url?: string;
  summary: string;
  evidenceLevel: 'High (Clinical Guidelines)' | 'Moderate (Literature Consensus)' | 'General Medical Reference';
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  image?: {
    url: string;
    name?: string;
  };
  citations?: Citation[];
  symptomSummary?: {
    location?: string;
    duration?: string;
    itchLevel?: number;
    painLevel?: number;
    isSpreading?: boolean;
  };
}

export interface SampleCase {
  id: string;
  title: string;
  category: string;
  description: string;
  imageUrl: string;
  symptoms: {
    location: string;
    duration: string;
    itchLevel: number;
    painLevel: number;
    isSpreading: boolean;
  };
  promptText: string;
}

export interface SymptomFilter {
  location: string;
  duration: string;
  itchLevel: number; // 0-10
  painLevel: number; // 0-10
  isSpreading: boolean;
  additionalNotes: string;
}

export interface AccessibilitySettings {
  fontSize: 'normal' | 'large' | 'xlarge';
  highContrast: boolean;
  dyslexicFont: boolean;
}

export interface ChatSession {
  id: string;
  title: string;
  isPublic?: boolean;
  canEdit?: boolean;
  createdAt: string;
  updatedAt: string;
  messages: ChatMessage[];
}
