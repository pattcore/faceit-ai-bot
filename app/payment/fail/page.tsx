'use client';

import Link from 'next/link';
import { useTranslation } from 'react-i18next';

export default function PaymentFailPage() {
  const { t } = useTranslation();

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 text-gray-900 dark:bg-gray-900 dark:text-white animate-fade-in">
      <div className="max-w-lg w-full mx-4 card text-center animate-fade-in-up">
        <div className="text-5xl mb-4">❌</div>
        <h1 className="text-3xl font-bold mb-3">
          {t('payment.fail_title', 'Payment failed')}
        </h1>
        <p className="text-gray-600 dark:text-gray-300 mb-8">
          {t('payment.fail_subtitle', 'Something went wrong while processing your payment. Please try again or contact support.')}
        </p>
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <Link href="/subscriptions" className="btn-primary w-full sm:w-auto">
            {t('payment.fail_button_retry', 'Try again')}
          </Link>
          <Link href="/" className="btn-secondary w-full sm:w-auto">
            {t('payment.fabutton_home', 'Back to home')}
          </Link>
        </div>
      </div>
    </div>
  );
}
