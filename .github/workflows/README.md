# GitHub Actions Workflows

## Предупреждения IDE о secrets

Предупреждения вида "Context access might be invalid" для secrets - это **нормально**.

IDE не может проверить существование GitHub Secrets, так как они:
- Хранятся в GitHub Settings → Secrets and variables → Actions
- Не доступны локально
- Не синхронизируются с репозиторием

### Настроенные secrets для этого проекта:

#### VPS Deploy (deploy-to-vps.yml)

**Обязательные:**
- `VPS_SSH_PRIVATE_KEY` - SSH приватный ключ для подключения к VPS

**Опциональные (есть значения по умолчанию):**
- `VPS_HOST` - хост VPS (по умолчанию: `pattmsc.online`)
- `VPS_USER` - пользователь SSH (по умолчанию: `root`)
- `VPS_PORT` - SSH порт (по умолчанию: `22`)
- `VPS_DEPLOY_PATH` - путь деплоя (по умолчанию: `/var/www/faceit-ai-bot`)

### Как настроить secrets:

1. Перейдите: https://github.com/pat1one/faceit-ai-bot/settings/secrets/actions
2. Нажмите "New repository secret"
3. Добавьте необходимые secrets

### Документация:

- Полная инструкция: `DEPLOY_PATTMSC_ONLINE.md`
- Общая для VPS: `VPS_SETUP.md`
- Общая для reg.ru: `DEPLOY_REGRU.md`
