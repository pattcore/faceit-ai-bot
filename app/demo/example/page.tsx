'use client';

import React from 'react';
import Link from 'next/link';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../../contexts/AuthContext';

const exampleCoachReportRu = {
  overview:
    'Матч на карте Mirage показал хороший базовый уровень игры: ты уверенно отыгрываешь большинство стандартных ситуаций, но теряешь много раундов из-за спешки, плохих таймингов и недооценки позиций оппонента.',
  strengths: [
    {
      title: 'Уверенная стрельба в простых дуэлях',
      description:
        'В ситуациях 5v5 и 4v4, когда у тебя есть поддержка команды, ты стабильно забираешь свои дуэли и не боишься контакта.',
    },
    {
      title: 'Понимание базовых таймингов',
      description:
        'Ты правильно используешь ранние тайминги для занятия мида и коннектора, что часто даёт контролируемый старт раунда.',
    },
  ],
  weaknesses: [
    {
      title: 'Открытые пики без трейда',
      description:
        'Слишком часто выходишь первым без флешек и поддержки, умираешь в соло и оставляешь команду в меньшинстве уже в начале раунда.',
    },
    {
      title: 'Недостаток дисциплины в клатчах',
      description:
        'В ситуациях 1vX ты торопишься, открываешься под несколько углов одновременно и не даёшь себе время переосмыслить позиционирование.',
    },
  ],
  key_moments: [
    {
      round: 7,
      title: 'Неудачный выход через мид без гранат',
      what_happened:
        'Вы вдвоём попытались занять мид без смоков на Window и Connector, в итоге сразу попали под перекрёстный огонь с AWP и rifler-а.',
      mistake:
        'Полный игнор обязательных смоков и флешек, выход на открытое пространство без информации по позициям соперника.',
      better_play:
        'Сначала дать смок на Window и Connector, затем под флешку пикать короткий угол. Либо дождаться контакта тиммейта с аплэнта, чтобы отвлечь внимание защиту.',
    },
    {
      round: 13,
      title: 'Проигранный клатч 1v2 на A-плэнте',
      what_happened:
        'После установки бомбы ты занял открытую позицию на default без возможности уйти в безопасный угол и был разменян с двух сторон.',
      mistake:
        'Отсутствие плана на послеплэнт и игра без использования таймера: ты остался в первой позиции, которую чаще всего проверяют.',
      better_play:
        'После постановки бомбы уйти в безопасную позицию (Firebox/Palace/Tetris), сыграть от звука дефьюза и таймера, вынуждая соперников ошибаться.',
    },
  ],
  training_plan: [
    {
      goal: 'Сократить количество бессмысленных смертей в начале раунда',
      exercises: [
        'Разобрать 5–10 своих демок и выписать все смерти в первые 20 секунд раунда с причиной (без флешки, без трейда, плохой пик).',
        'Перед каждым матчем напоминать себе правило: не открываться первым без гранат и поддержки, если нет чёткого плана.',
        'Потренировать стандартные выходы с тиммейтом: один даёт флешку, второй пикает — сначала на DM/паблик серверах, затем в рейтинге.',
      ],
    },
    {
      goal: 'Улучшить игру в клатчах 1v2 и 1v3',
      exercises: [
        'Посмотреть 3–5 профессиональных демок на Mirage и отдельно обратить внимание на решения игроков в клатчах (позиции после установки бомбы, использование таймера).',
        'В собственных демках помечать все клатч-ситуации и возвращаться к ним: что можно было сделать спокойнее и надёжнее.',
        'На тренировках осознанно отыгрывать клатчи: не спешить, всегда задавать себе вопрос «где могу безопасно отойти после размена?».',
      ],
    },
  ],
  summary:
    'В целом у тебя уже есть фундамент для уверенной игры на своём уровне. Основной буст рейтинга придёт не от «идеального аима», а от дисциплины: меньше бессмысленных смертей, более грамотные выходы с командой и продуманные клатчи. Если внедришь эти изменения в игру, уже через 2–3 недели можно ожидать стабильный рост по Faceit ELO.',
};

const exampleCoachReportEn = {
  overview:
    'A Mirage match showed a solid baseline level: you handle most standard situations confidently, but lose many rounds because of rushing decisions, bad timings, and underestimating enemy positions.',
  strengths: [
    {
      title: 'Confident aim in simple duels',
      description:
        'In 5v5 and 4v4 situations when you have teammates nearby, you reliably win your duels and are not afraid of contact.',
    },
    {
      title: 'Understanding of basic timings',
      description:
        'You use early timings correctly to take mid and connector control, which often gives a stable start to the round.',
    },
  ],
  weaknesses: [
    {
      title: 'Dry peeks without trade',
      description:
        'You often swing first without flashes or support, die alone, and leave your team in a 4v5 early in the round.',
    },
    {
      title: 'Lack of discipline in clutch situations',
      description:
        'In 1vX situations you hurry, wide-swing into multiple angles at once, and do not give yourself time to reposition or reset the fight.',
    },
  ],
  key_moments: [
    {
      round: 7,
      title: 'Failed mid take without utility',
      what_happened:
        'You and a teammate tried to take mid without smokes on Window and Connector and immediately fell under crossfire from an AWP and a rifler.',
      mistake:
        'Ignoring essential smokes and flashes and swinging into open space with no information about enemy positions.',
      better_play:
        'First throw smokes for Window and Connector, then peek the short angle under a flash. Alternatively, wait for contact from A site to split defenders’ attention.',
    },
    {
      round: 13,
      title: 'Lost 1v2 clutch on A site',
      what_happened:
        'After planting the bomb you stayed in an open default position with no way to fall back and were traded from two sides.',
      mistake:
        'No post-plant plan and no use of the timer: you stayed in the first obvious position that is usually cleared.',
      better_play:
        'After planting, move to a safer position (Firebox/Palace/Tetris), play off the defuse sound and the bomb timer, forcing opponents to make mistakes.',
    },
  ],
  training_plan: [
    {
      goal: 'Reduce pointless early-round deaths',
      exercises: [
        'Review 5–10 of your demos and write down all deaths in the first 20 seconds of the round with the reason (no flash, no trade, bad peek).',
        'Before each match, remind yourself: do not peek first without utility and support unless there is a clear plan.',
        'Practice standard executions with a teammate: one throws the flash, the other peeks – first on DM/public servers, then in ranked games.',
      ],
    },
    {
      goal: 'Improve 1v2 and 1v3 clutch play',
      exercises: [
        'Watch 3–5 pro demos on Mirage and focus on how players play out clutch situations (post-plant positions, use of the timer).',
        'Mark all of your own clutch situations in demos and review them: what could have been done more calmly and reliably.',
        'During practice, consciously play clutches: do not rush, always ask yourself “where can I fall back safely after the trade?”.',
      ],
    },
  ],
  summary:
    'You already have a solid foundation for your current level. The main ELO boost will not come from “perfect aim” but from discipline: fewer pointless deaths, better coordinated executions with the team, and smarter clutch decisions. If you implement these changes, you can expect a stable Faceit ELO increase within 2–3 weeks.',
};

export default function DemoExamplePage() {
  const { t, i18n } = useTranslation();
  const { user } = useAuth();

  const lang = i18n.language && i18n.language.toLowerCase().startsWith('en') ? 'en' : 'ru';
  const coachReport = lang === 'en' ? exampleCoachReportEn : exampleCoachReportRu;

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gray-50 text-gray-900 dark:bg-gray-900 dark:text-white animate-fade-in">
      <div className="text-center">
        <div className="max-w-4xl mx-auto">
          <h1 className="text-5xl font-bold mb-4 bg-gradient-to-r from-orange-500 to-orange-600 bg-clip-text text-transparent">
            📊
            {t('demo_example.title', {
              defaultValue:
                lang === 'en' ? 'Demo analysis example' : 'Пример анализа демки',
            })}
          </h1>
          <p className="text-xl text-gray-300 mb-8">
            {t('demo_example.subtitle', {
              defaultValue:
                lang === 'en'
                  ? 'This is how an AI coach report for one of your demos might look. This is an example; the real analysis will be based on your own games.'
                  : 'Так может выглядеть отчёт от ИИ-коуча по одной твоей демке. Это пример, реальный анализ будет строиться по твоей игре.',
            })}
          </p>

          <div className="mt-4 text-left max-h-[600px] overflow-auto text-sm card">
            <h2 className="text-lg font-semibold mb-2">
              {t('demo.results', { defaultValue: 'Результаты анализа' })}
            </h2>

            <div className="space-y-4">
              {coachReport.overview && (
                <p className="text-sm text-zinc-300 mb-2">{coachReport.overview}</p>
              )}

              {coachReport.strengths && coachReport.strengths.length > 0 && (
                <div>
                  <h3 className="font-semibold mb-1">
                    {t('demo.coach_strengths', {
                      defaultValue:
                        lang === 'en' ? 'Strengths' : 'Сильные стороны',
                    })}
                  </h3>
                  <ul className="list-disc list-inside space-y-1 text-sm">
                    {coachReport.strengths.map((s: any, idx: number) => (
                      <li key={idx}>
                        <span className="font-medium">{s.title}: </span>
                        <span>{s.description}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {coachReport.weaknesses && coachReport.weaknesses.length > 0 && (
                <div>
                  <h3 className="font-semibold mb-1">
                    {t('demo.coach_weaknesses', {
                      defaultValue:
                        lang === 'en' ? 'Weaknesses' : 'Слабые стороны',
                    })}
                  </h3>
                  <ul className="list-disc list-inside space-y-1 text-sm">
                    {coachReport.weaknesses.map((w: any, idx: number) => (
                      <li key={idx}>
                        <span className="font-medium">{w.title}: </span>
                        <span>{w.description}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {coachReport.key_moments && coachReport.key_moments.length > 0 && (
                <div>
                  <h3 className="font-semibold mb-1">
                    {t('demo.coach_key_moments', {
                      defaultValue:
                        lang === 'en' ? 'Key moments' : 'Ключевые моменты',
                    })}
                  </h3>
                  <ul className="space-y-1 text-sm">
                    {coachReport.key_moments.map((m: any, idx: number) => (
                      <li key={idx} className="border border-zinc-700 rounded-md p-2">
                        <div className="text-xs text-zinc-400 mb-1">
                          {t('demo.round_label', {
                            defaultValue: lang === 'en' ? 'Round' : 'Раунд',
                          })}{' '}
                          {m.round}
                        </div>
                        <div className="font-medium mb-1">{m.title}</div>
                        <div className="text-xs text-zinc-300 mb-1">{m.what_happened}</div>
                        <div className="text-xs text-red-300 mb-1">{m.mistake}</div>
                        <div className="text-xs text-emerald-300">{m.better_play}</div>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {coachReport.training_plan && coachReport.training_plan.length > 0 && (
                <div>
                  <h3 className="font-semibold mb-1">
                    {t('demo.coach_training_plan', {
                      defaultValue:
                        lang === 'en' ? 'Training plan' : 'План тренировок',
                    })}
                  </h3>
                  <ul className="space-y-2 text-sm">
                    {coachReport.training_plan.map((p: any, idx: number) => (
                      <li key={idx} className="border border-zinc-700 rounded-md p-2">
                        <div className="font-medium mb-1">{p.goal}</div>
                        {p.exercises && (
                          <ul className="list-disc list-inside text-xs text-zinc-300 space-y-1">
                            {p.exercises.map((ex: string, exIdx: number) => (
                              <li key={exIdx}>{ex}</li>
                            ))}
                          </ul>
                        )}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {coachReport.summary && (
                <p className="text-sm text-zinc-200">{coachReport.summary}</p>
              )}
            </div>
          </div>

          <div className="mt-8 flex justify-center gap-4">
            <Link href={user ? '/demo' : '/auth'} className="btn-primary">
              {t('landing.cta_get_started', {
                defaultValue: lang === 'en' ? 'Get started' : 'Начать',
              })}
            </Link>
            <Link href="/demo" className="btn-primary">
              {t('demo.title', { defaultValue: lang === 'en' ? 'Demo analysis' : 'Анализ демки' })}
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
