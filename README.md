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
1. Клонируйте репозиторий: `git clone https://github.com/LordKoks/321.git`
2. Соберите Docker образ: `docker build -t openhands-agent-server .`
3. Запустите сервер: `docker run -d -p 8000:8000 openhands-agent-server`
4. Установите VS Code extension: `code --install-extension vscode-acp-1.3.0.vsix`
5. Для web UI: `cd openhands/examples/ui_with_chainlit && chainlit run app.py`
6. Для APK: Установите Android SDK, затем `cd mobile-app && npx cap build android`

## Скачивание APK
APK файл генерируется после сборки: `mobile-app/android/app/build/outputs/apk/debug/app-debug.apk`

Команда для скачивания через SSH:  
`scp username@server_ip:/path/to/repo/mobile-app/android/app/build/outputs/apk/debug/app-debug.apk /local/path`

Или скачайте из releases репозитория (если опубликован).

## Лицензия
MIT для OpenHands/MetaGPT, Apache для VS Code parts.

## Контакты
Для вопросов: создайте issue в репозитории.