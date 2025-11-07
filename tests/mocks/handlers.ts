import { http, HttpResponse, delay } from 'msw';

export const handlers = [
  http.post('http://localhost:8000/analyze-demo', async () => {
    await delay(100);
    return HttpResponse.json({ 
      analysis: 'Demo analysis result',
      error: null
    });
  }),

  http.post('http://localhost:8000/payments/yookassa', async () => {
    await delay(50);
    return HttpResponse.json({ payment_url: 'http://payment-link.com' });
  }),

  http.post('http://localhost:8000/payments/sbp', async () => {
    await delay(50);
    return HttpResponse.json({ payment_url: 'http://sbp-payment-link.com' });
  })
];