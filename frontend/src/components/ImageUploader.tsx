import React, { useRef, useState } from 'react';
import { Upload, Camera, Image as ImageIcon, X, AlertCircle, Check } from 'lucide-react';

interface ImageUploaderProps {
  onImageSelected: (base64Url: string, file: File) => void;
  selectedImage: string | null;
  onClearImage: () => void;
}

export const ImageUploader: React.FC<ImageUploaderProps> = ({
  onImageSelected,
  selectedImage,
  onClearImage,
}) => {
  const [isDragging, setIsDragging] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFile = (file: File) => {
    if (!file.type.startsWith('image/')) {
      setErrorMsg('Please upload a valid image file (JPEG, PNG, WEBP).');
      return;
    }
    if (file.size > 10 * 1024 * 1024) {
      setErrorMsg('Image file size exceeds 10MB limit.');
      return;
    }

    setErrorMsg(null);
    const reader = new FileReader();
    reader.onload = () => {
      if (typeof reader.result === 'string') {
        onImageSelected(reader.result, file);
      }
    };
    reader.readAsDataURL(file);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0]);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  return (
    <div className="space-y-2">
      {selectedImage ? (
        <div className="relative inline-block group rounded-xl overflow-hidden border border-teal-500 bg-white p-1.5 shadow-sm">
          <img
            src={selectedImage}
            alt="Skin concern preview"
            className="h-24 w-24 sm:h-28 sm:w-28 object-cover rounded-lg"
          />
          <button
            onClick={onClearImage}
            className="absolute top-2 right-2 p-1 bg-slate-900/80 hover:bg-rose-600 text-white rounded-full transition-colors shadow-md"
            title="Remove uploaded image"
          >
            <X className="w-3.5 h-3.5" />
          </button>
          <div className="absolute bottom-2 left-2 right-2 bg-slate-900/90 text-teal-300 text-[10px] px-1.5 py-0.5 rounded text-center font-bold">
            Photo Attached ✓
          </div>
        </div>
      ) : (
        <div
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onClick={() => fileInputRef.current?.click()}
          className={`cursor-pointer border-2 border-dashed rounded-xl p-3 sm:p-4 text-center transition-all flex flex-col items-center justify-center gap-1.5 ${
            isDragging
              ? 'border-teal-500 bg-teal-50 scale-[1.01]'
              : 'border-slate-200 hover:border-teal-500/70 bg-slate-50/60 hover:bg-white shadow-2xs'
          }`}
        >
          <input
            type="file"
            ref={fileInputRef}
            onChange={(e) => e.target.files?.[0] && handleFile(e.target.files[0])}
            accept="image/*"
            className="hidden"
          />

          <div className="w-8 h-8 rounded-full bg-teal-100 text-teal-700 flex items-center justify-center">
            <Upload className="w-4 h-4" />
          </div>

          <div>
            <p className="text-xs font-bold text-slate-800">
              Upload Skin Photo / Lesion
            </p>
            <p className="text-[10px] text-slate-500 mt-0.5">
              Drag & drop or click to upload (JPEG, PNG • Max 10MB)
            </p>
          </div>
        </div>
      )}

      {errorMsg && (
        <div className="text-[11px] text-rose-700 font-medium flex items-center gap-1 bg-rose-50 p-2 rounded-lg border border-rose-200">
          <AlertCircle className="w-3.5 h-3.5 shrink-0 text-rose-600" />
          <span>{errorMsg}</span>
        </div>
      )}
    </div>
  );
};
