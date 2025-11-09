# 🌐 Локализация / Localization

Файлы переводов для интернационализации проекта.  
Translation files for project internationalization.

## 📁 Файлы / Files

- `ru.json` - Русский язык / Russian language
- `en.json` - Английский язык / English language

## 🔧 Использование / Usage

### С Next.js и react-i18next

1. Установите зависимости:

```bash
npm install react-i18next i18next next-i18next
```

1. Создайте конфигурацию `i18n.ts`:

```typescript
import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import en from './locales/en.json';
import ru from './locales/ru.json';

i18n
  .use(initReactI18next)
  .init({
    resources: {
      en: { translation: en },
      ru: { translation: ru }
    },
    lng: 'ru', // язык по умолчанию
    fallbackLng: 'en',
    interpolation: {
      escapeValue: false
    }
  });

export default i18n;
```

1. Используйте в компонентах:

```typescript
import { useTranslation } from 'react-i18next';

function MyComponent() {
  const { t } = useTranslation();
  
  return (
    <div>
      <h1>{t('player.title')}</h1>
      <p>{t('player.subtitle')}</p>
    </div>
  );
}
```

### Переключение языка / Language Switching

```typescript
import { useTranslation } from 'react-i18next';

function LanguageSwitcher() {
  const { i18n } = useTranslation();
  
  return (
    <button onClick={() => i18n.changeLanguage(i18n.language === 'ru' ? 'en' : 'ru')}>
      {i18n.language === 'ru' ? '🇬🇧 EN' : '🇷🇺 RU'}
    </button>
  );
}
```

## 📝 Добавление новых переводов / Adding New Translations

1. Добавьте ключ в оба файла (ru.json и en.json)
2. Используйте в коде: `t('yourKey')`

## 🔍 Структура / Structure

```text
locales/
├── en.json          # English translations
├── ru.json          # Russian translations
└── README.md        # This file
```

---

**Документация i18next:** https://www.i18next.com/  
**Документация react-i18next:** https://react.i18next.com/
