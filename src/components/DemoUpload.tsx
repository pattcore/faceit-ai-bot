import React from 'react';

type AnalysisResult = {
  filename: string;
  status: string;
  message?: string;
};

type Props = {
  onAnalysisComplete?: (result: File | AnalysisResult) => void;
};

export default function DemoUpload({ onAnalysisComplete }: Props) {
  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const form = e.currentTarget;
    const fileInput = form.querySelector('input[type="file"]') as HTMLInputElement;
    const file = fileInput?.files?.[0];
    
    if (file && onAnalysisComplete) {
      onAnalysisComplete(file);
    }
  };

  return (
    <form onSubmit={handleSubmit} style={{textAlign: 'center'}}>
      <input type="file" accept=".dem" aria-label="Загрузить демо файл" />
      <div style={{marginTop: 12}}>
        <button type="submit">Загрузить и проанализировать</button>
      </div>
    </form>
  );
}
