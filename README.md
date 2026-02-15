# AI Agent Orchestrator: MetaGPT + OpenHands + VS Code Integration

Этот проект представляет собой интеграцию MetaGPT (multi-agent фреймворк для генерации софта) с OpenHands Agent Server, подключённую к VS Code через ACP/MCP extension. Система работает как единый оркестр AI-агентов для автоматизации разработки.

**Репозиторий полный: Все компоненты (MetaGPT, OpenHands, VS Code ACP) включены напрямую, без submodules. Клонируй и запускай сразу.**

## Особенности
- **Единая система**: MetaGPT интегрирован в OpenHands как инструмент, всё в одном Docker контейнере.
- **VS Code Extension**: ACP extension для чата с агентами в IDE.
- **Web версия**: UI на базе Chainlit для взаимодействия через браузер.
- **Мобильная версия**: Android APK для доступа к агентам на мобильных устройствах.
- **Совместимость**: Python 3.11, разрешены конфликты зависимостей (tenacity обновлён).

## Структура проекта
- `metagpt/`: Исходный код MetaGPT (форк с обновлениями).
- `openhands/`: OpenHands SDK и Agent Server с интеграцией MetaGPT.
- `vscode-acp/`: ACP extension для VS Code.
- `mobile-app/`: Capacitor проект для Android APK.
- `Dockerfile`: Образ с интегрированным агентом.
- `integration_map.md`: Детали интеграции.

## Установка и запуск

**На локальной машине (Windows/Mac/Linux):**
1. Клонируйте репозиторий: `git clone https://github.com/LordKoks/321.git`
2. Убедитесь, что установлены:
   - Docker Desktop
   - Node.js (для mobile-app)
   - VS Code

**В контейнере (рекомендуется для полного функционала):**
1. Соберите Docker образ: `docker build -t openhands-agent-server .`
2. Запустите сервер: `docker run -d -p 8000:8000 openhands-agent-server`

**Web UI (Chainlit):**
```bash
cd metagpt/examples/ui_with_chainlit
chainlit run app.py
```
Откройте http://localhost:8000 в браузере

**VS Code Extension (ACP):**
```bash
# В VS Code откройте terminal и выполните:
code --install-extension ./vscode-acp-1.3.0.vsix
```

**Mobile APK (Android):**
```bash
cd mobile-app
npm install
npx cap build android
```
APK находится в: `mobile-app/android/app/build/outputs/apk/debug/app-debug.apk`

## Системные требования
- Python 3.11+
- Docker Desktop (макOS/Windows) или Docker Engine (Linux)
- Node.js 16+ (для мобильного приложения)
- Android SDK (для сборки APK)
- Git

## Скачивание APK
APK генерируется после успешной сборки: `mobile-app/android/app/build/outputs/apk/debug/app-debug.apk`

**Если разрабатываете на Windows:**
- Используйте Git Bash вместо PowerShell для команд с `&&`
- Или замените `&&` на `;` для PowerShell

**Скачивание через SSH:**  
```bash
scp username@server_ip:/path/to/repo/mobile-app/android/app/build/outputs/apk/debug/app-debug.apk /local/path
```

## Устранение проблем
| Проблема | Решение |
|---------|--------|
| `docker: command not found` | Установите Docker Desktop или Docker Engine |
| `code: command not found` | Добавьте VS Code в PATH: https://code.visualstudio.com/docs/setup/setup-overview |
| `chainlit: command not found` | `pip install chainlit` |
| `npx: command not found` | Установите Node.js с npm |
| `Path not found` на Windows | Используйте обратные слеши или кавычки: `"metagpt\examples\ui_with_chainlit"` |

## Лицензия
MIT для OpenHands/MetaGPT, Apache для VS Code parts.

## Контакты
Для вопросов: создайте issue в репозитории.