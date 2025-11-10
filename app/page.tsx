'use client';

import React, { useState } from 'react';
import PlayerAnalysis from './components/PlayerAnalysis';
import DemoUpload from '../src/components/DemoUpload';
import TeammateChat from '../src/components/TeammateChat';
import NotificationSystem from '../src/components/NotificationSystem';
import { API_ENDPOINTS } from '../src/config/api';

interface AnalysisResult {
  filename?: string;
  status?: string;
  message?: string;
  error?: string;
  [key: string]: any;
}

export default function DemoPage() {
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [paymentUrl, setPaymentUrl] = useState<string | null>(null);

  const handleAnalysisComplete = async (result: File | AnalysisResult) => {
    setLoading(true);
    try {
      // If it's a File, send for analysis
      if (result instanceof File) {
        const formData = new FormData();
        formData.append('demo', result);

        const response = await fetch(API_ENDPOINTS.DEMO_ANALYZE, {
          method: 'POST',
          body: formData,
        });

        const analysisData = await response.json();
        setAnalysisResult(analysisData);
      } else {
        // If it's already analysis result
        setAnalysisResult(result);
      }
    } catch (error) {
      console.error('Error during analysis:', error);
    } finally {
      setLoading(false);
    }
  };

  const handlePayment = async () => {
    try {
      const response = await fetch(API_ENDPOINTS.PAYMENTS_CREATE, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          amount: 500,
          currency: 'RUB',
          description: 'Demo analysis payment',
          provider: 'YOOKASSA',
        }),
      });

      const paymentData = await response.json();
      setPaymentUrl(paymentData.payment_url);
    } catch (error) {
      console.error('Error during payment:', error);
    }
  };

  const handleSBPPayment = async () => {
    try {
      const response = await fetch(API_ENDPOINTS.PAYMENTS_CREATE, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          amount: 500,
          currency: 'RUB',
          description: 'Demo analysis payment via SBP',
          provider: 'SBP',
        }),
      });

      const paymentData = await response.json();
      setPaymentUrl(paymentData.payment_url);
    } catch (error) {
      console.error('Error during SBP payment:', error);
      alert('SBP payment error. Please try again.');
    }
  };

  return (
    <div className="page-container">
      <PlayerAnalysis />

      <div className="page-header mt-12">
        <h2 className="text-2xl font-bold text-white mb-4">📊 Demo File Analysis</h2>
        <p>Upload demo for detailed analysis</p>
      </div>

      <DemoUpload onAnalysisComplete={handleAnalysisComplete} />

      {loading && <p>Analyzing demo...</p>}

      {analysisResult && (
        <div className="analysis-result">
          <h3>Analysis Results</h3>
          <pre>{JSON.stringify(analysisResult, null, 2)}</pre>
          <button onClick={handlePayment} className="btn btn-primary">Pay via YooKassa</button>
          <button onClick={handleSBPPayment} className="btn btn-secondary">Pay via SBP</button>
        </div>
      )}

      {paymentUrl && (
        <div className="payment-link">
          <p>Go to payment link:</p>
          <a href={paymentUrl} target="_blank" rel="noopener noreferrer">Pay</a>
        </div>
      )}

      <TeammateChat />
      <NotificationSystem />

      <style>{`
        .page-container {
          min-height: 100vh;
          padding: 2rem 0;
          background: linear-gradient(135deg, #0c0c0c 0%, #1a1a1a 100%);
        }

        .page-header {
          text-align: center;
          margin-bottom: 3rem;
        }

        .page-header h1 {
          font-size: 3rem;
          font-weight: 800;
          margin-bottom: 1rem;
          background: linear-gradient(45deg, #ff5200, #ffaa00);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          background-clip: text;
        }

        .page-header p {
          font-size: 1.2rem;
          color: #a1a1aa;
          max-width: 600px;
          margin: 0 auto;
          line-height: 1.6;
        }

        .analysis-result {
          margin-top: 2rem;
          padding: 1rem;
          background: rgba(255, 255, 255, 0.05);
          border-radius: 8px;
          color: #fafafa;
        }

        .analysis-result pre {
          white-space: pre-wrap;
          word-wrap: break-word;
        }

        .btn {
          margin-top: 1rem;
          padding: 0.5rem 1rem;
          background: #ff5200;
          color: white;
          border: none;
          border-radius: 4px;
          cursor: pointer;
        }

        .btn:hover {
          background: #ffaa00;
        }

        .btn-secondary {
          margin-top: 1rem;
          padding: 0.5rem 1rem;
          background: #007bff;
          color: white;
          border: none;
          border-radius: 4px;
          cursor: pointer;
        }

        .btn-secondary:hover {
          background: #0056b3;
        }

        .payment-link {
          margin-top: 2rem;
          padding: 1rem;
          background: rgba(255, 255, 255, 0.05);
          border-radius: 8px;
          color: #fafafa;
        }

        .payment-link a {
          color: #ffaa00;
          text-decoration: none;
        }

        .payment-link a:hover {
          text-decoration: underline;
        }

        .feature-item p {
          color: #a1a1aa;
          font-size: 0.9rem;
          line-height: 1.4;
        }      `}</style>    </div>  );}