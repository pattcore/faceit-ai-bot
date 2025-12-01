'use client';

import Link from 'next/link';

export default function ExtensionPage() {
  return (
    <div className="min-h-screen bg-gray-50 text-gray-900 dark:bg-gray-900 dark:text-white flex items-center justify-center animate-fade-in">
      <div className="max-w-3xl w-full mx-auto px-6 py-16">
        <h1 className="text-4xl md:text-5xl font-bold mb-4 bg-gradient-to-r from-orange-500 to-yellow-500 bg-clip-text text-transparent">
          Браузерное расширение Faceit AI Bot
        </h1>
        <p className="text-lg text-gray-400 mb-8">
          Быстрый доступ к анализу игроков CS2 и демкам Faceit прямо из браузера. Расширение
          использует отдельный API-токен вашего аккаунта Faceit AI Bot, которым вы управляете
          прямо в попапе (вход по email и паролю).
        </p>

        <div className="mb-8">
          <a
            href="/assets/prod/faceit-ai-bot-extension.zip"
            className="btn-primary inline-flex items-center justify-center px-6 py-3 text-base font-semibold"
          >
            Download browser extension (ZIP)
          </a>
          <p className="mt-2 text-sm text-gray-400">
            Latest Faceit AI Bot browser extension build for Chrome, Edge and Opera. Install via
            your browser's developer mode.
          </p>
        </div>

        <div className="space-y-8">
          <section className="card">
            <h2 className="text-2xl font-semibold mb-3">Возможности</h2>
            <ul className="list-disc list-inside space-y-2 text-gray-200">
              <li>Открывать Faceit AI Bot в один клик из панели браузера.</li>
              <li>Запускать анализ игрока прямо со страницы профиля на Faceit.</li>
              <li>Переходить с профиля Steam Community на сайт Faceit AI Bot.</li>
            </ul>
          </section>

          <section className="card">
            <h2 className="text-2xl font-semibold mb-3">
              Установка расширения вручную (Chrome / Edge / Opera)
            </h2>
            <ol className="list-decimal list-inside space-y-2 text-gray-200 text-sm md:text-base">
              <li>
                Зайдите на{' '}
                <a
                  href="https://github.com/pat1one/faceit-ai-bot"
                  target="_blank"
                  rel="noreferrer"
                  className="text-orange-400 hover:text-orange-300 underline"
                >
                  GitHub репозиторий Faceit AI Bot
                </a>{' '}
                и скачайте код (кнопка <code>Code → Download ZIP</code>) или клонируйте репозиторий.
              </li>
              <li>Распакуйте архив (если скачивали ZIP).</li>
              <li>
                Откройте в браузере:
                <ul className="list-disc list-inside ml-5 mt-1 space-y-1 text-gray-300">
                  <li><code>chrome://extensions</code> — для Google Chrome</li>
                  <li><code>edge://extensions</code> — для Microsoft Edge</li>
                  <li><code>opera://extensions</code> — для Opera</li>
                </ul>
              </li>
              <li>Включите «Режим разработчика» (Developer mode).</li>
              <li>
                Нажмите «Загрузить распакованное» / «Load unpacked» и выберите папку
                <code className="mx-1">extension</code> внутри проекта <code>faceit-ai-bot</code>.
              </li>
              <li>
                Убедитесь, что расширение <strong>Faceit AI Bot Assistant</strong> включено и, при
                желании, закрепите иконку на панели браузера.
              </li>
              <li>
                Если у вас ещё нет аккаунта, зарегистрируйтесь на сайте{' '}
                <a
                  href="https://pattmsc.online"
                  target="_blank"
                  rel="noreferrer"
                  className="text-orange-400 hover:text-orange-300 underline"
                >
                  pattmsc.online
                </a>
                . Затем нажмите на иконку расширения, в открывшемся попапе войдите в аккаунт по
                email и паролю — расширение сохранит отдельный API-токен и покажет доступные
                действия (анализ аккаунта, демо и поиск тиммейтов).
              </li>
            </ol>
          </section>

          <section className="card">
            <h2 className="text-2xl font-semibold mb-3">Полезные ссылки</h2>
            <ul className="space-y-2 text-gray-200">
              <li>
                Сайт: {' '}
                <a
                  href="https://pattmsc.online"
                  target="_blank"
                  rel="noreferrer"
                  className="text-orange-400 hover:text-orange-300 underline"
                >
                  pattmsc.online
                </a>
              </li>
              <li>
                Репозиторий: {' '}
                <a
                  href="https://github.com/pat1one/faceit-ai-bot"
                  target="_blank"
                  rel="noreferrer"
                  className="text-orange-400 hover:text-orange-300 underline"
                >
                  github.com/pat1one/faceit-ai-bot
                </a>
              </li>
            </ul>
          </section>

          <div className="flex flex-wrap gap-3">
            <Link href="/" className="btn-primary">
              На главную
            </Link>
            <Link href="/analysis" className="btn-primary">
              Перейти к анализу игрока
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
