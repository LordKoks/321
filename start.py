#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║          LordKoks/321 — ЕДИНАЯ СИСТЕМА ЗАПУСКА / ADMIN LAUNCHER             ║
║                                                                              ║
║  Запуск:   python start.py                                                   ║
║  Требует:  Python 3.8+, Docker Desktop / Docker Engine                       ║
╚══════════════════════════════════════════════════════════════════════════════╝

ОПИСАНИЕ ПРОЕКТА (нельзя изменить — зашито в константу READ_ONLY_DESCRIPTION)
──────────────────────────────────────────────────────────────────────────────

Репозиторий LordKoks/321 состоит из двух основных частей:

1. Landing Page (index.html / admin.html) — статические HTML-файлы в корне.
   Дизайн-система Neubrutalism: жирные 2px границы, hard pixel shadows, dot-grid
   фон с parallax, OLED dark mode. Работают без сервера.

2. social-api/ — REST API на FastAPI для автоматизации SMM-рекламы:
   • PostgreSQL 16 — основная БД (модели: User, Post, Campaign, SocialAccount, Analytics)
   • Redis 7 — брокер Celery и кеш
   • FastAPI (uvicorn) :8000 — REST API, Swagger UI /docs
   • Celery Worker — фоновая публикация постов в соцсети
   • Celery Beat — планировщик (публикация каждые 60с, аналитика каждый час)
   • Nginx :80 — reverse proxy → API
   Интеграции: VK, X (Twitter), Telegram, OK, YouTube
   Агрегаторы вакансий: Glassdoor, Himalayas, Jobicy, TheirStack, SerpApi
"""

# ─────────────────────────────────────────────────────────────────────────────
# READ-ONLY ОПИСАНИЕ — КОНСТАНТА, НЕ ИЗМЕНЯЕМАЯ ИЗ МЕНЮ
# (используйте только для чтения; изменение требует правки исходного кода)
# ─────────────────────────────────────────────────────────────────────────────
READ_ONLY_DESCRIPTION: tuple[str, ...] = (
    "══════════════════════════════════════════════════════════════════",
    "  РЕПОЗИТОРИЙ: LordKoks/321",
    "  https://github.com/LordKoks/321",
    "══════════════════════════════════════════════════════════════════",
    "",
    "  ▸ index.html  — публичный лендинг AI Agent Orchestrator.",
    "    Neubrutalism-дизайн, Vanilla JS, без сборщика.",
    "    Разделы: Hero · Stats · Marquee · How It Works · Projects · Kanban",
    "",
    "  ▸ admin.html  — единая HTML-панель управления (браузер).",
    "    Копирование команд, live health-ping, энциклопедия, API-карта.",
    "",
    "  ▸ social-api/ — REST API для SMM-автоматизации.",
    "    Стек: FastAPI · SQLAlchemy · Alembic · Celery · Redis · Nginx",
    "    Auth: JWT (access 30мин + refresh 7дней), bcrypt пароли",
    "    Соцсети: VK · X (Twitter) · Telegram · OK · YouTube",
    "    Вакансии: Glassdoor · Himalayas · Jobicy · TheirStack · SerpApi",
    "    Тесты:  pytest, 7 файлов (auth/accounts/posts/campaigns/analytics/jobs/infra)",
    "",
    "  ▸ Docker Compose (social-api/docker-compose.yml) — 6 сервисов:",
    "    db (postgres:16) · redis (redis:7) · api (:8000) ·",
    "    worker (celery) · beat (celery-beat) · nginx (:80)",
    "",
    "══════════════════════════════════════════════════════════════════",
)

# ─────────────────────────────────────────────────────────────────────────────

import os
import sys
import shutil
import subprocess
import threading
import time
import textwrap
from pathlib import Path
from typing import Optional

# ── Цвета ANSI ───────────────────────────────────────────────────────────────
RESET  = "\033[0m"
BOLD   = "\033[1m"
DIM    = "\033[2m"
RED    = "\033[31m"
GREEN  = "\033[32m"
YELLOW = "\033[33m"
BLUE   = "\033[34m"
CYAN   = "\033[36m"
WHITE  = "\033[37m"
BG_BLK = "\033[40m"

ROOT = Path(__file__).parent.resolve()
API_DIR = ROOT / "social-api"


# ─────────────────────────────────────────────────────────────────────────────
# УТИЛИТЫ
# ─────────────────────────────────────────────────────────────────────────────

def _has(cmd: str) -> bool:
    return shutil.which(cmd) is not None


def _c(color: str, text: str, bold: bool = False) -> str:
    b = BOLD if bold else ""
    return f"{b}{color}{text}{RESET}"


def _hr(char: str = "─", width: int = 68) -> str:
    return char * width


def _clear() -> None:
    os.system("cls" if sys.platform == "win32" else "clear")


def _run(
    cmd: list[str],
    cwd: Optional[Path] = None,
    capture: bool = False,
) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd,
        cwd=str(cwd or ROOT),
        capture_output=capture,
        text=True,
    )


def _run_live(cmd: list[str], cwd: Optional[Path] = None) -> int:
    """Запустить команду с выводом в терминал; вернуть код возврата."""
    proc = subprocess.run(cmd, cwd=str(cwd or ROOT))
    return proc.returncode


def _spin(stop_event: threading.Event, msg: str) -> None:
    frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    i = 0
    while not stop_event.is_set():
        sys.stdout.write(f"\r{CYAN}{frames[i % len(frames)]}{RESET} {msg}  ")
        sys.stdout.flush()
        i += 1
        time.sleep(0.1)
    sys.stdout.write("\r" + " " * (len(msg) + 6) + "\r")
    sys.stdout.flush()


def _with_spinner(msg: str, fn, *args, **kwargs):
    ev = threading.Event()
    t = threading.Thread(target=_spin, args=(ev, msg), daemon=True)
    t.start()
    result = fn(*args, **kwargs)
    ev.set()
    t.join()
    return result


def _pause() -> None:
    input(f"\n{DIM}  Нажмите Enter чтобы вернуться в меню…{RESET}")


def _ok(msg: str) -> None:
    print(f"  {GREEN}✔{RESET}  {msg}")


def _err(msg: str) -> None:
    print(f"  {RED}✘{RESET}  {msg}")


def _warn(msg: str) -> None:
    print(f"  {YELLOW}⚠{RESET}  {msg}")


def _info(msg: str) -> None:
    print(f"  {BLUE}ℹ{RESET}  {msg}")


# ─────────────────────────────────────────────────────────────────────────────
# ПРОВЕРКА ЗАВИСИМОСТЕЙ
# ─────────────────────────────────────────────────────────────────────────────

def _check_deps() -> dict[str, bool]:
    return {
        "docker":         _has("docker"),
        "docker compose": _has("docker") and _run(
            ["docker", "compose", "version"], capture=True
        ).returncode == 0,
        "python3":        _has("python3") or _has("python"),
        "pytest":         _has("pytest"),
    }


# ─────────────────────────────────────────────────────────────────────────────
# ШАПКА
# ─────────────────────────────────────────────────────────────────────────────

def _header() -> None:
    print()
    print(_c(CYAN, "  ╔" + "═" * 66 + "╗", bold=True))
    print(_c(CYAN, "  ║", bold=True) +
          _c(WHITE, "       LordKoks/321  —  ЕДИНАЯ СИСТЕМА ЗАПУСКА              ", bold=True) +
          _c(CYAN, "║", bold=True))
    print(_c(CYAN, "  ║", bold=True) +
          _c(DIM,  "         python start.py  ·  https://github.com/LordKoks/321 ") +
          _c(CYAN, "║", bold=True))
    print(_c(CYAN, "  ╚" + "═" * 66 + "╝", bold=True))
    print()


# ─────────────────────────────────────────────────────────────────────────────
# ФУНКЦИИ ЗАПУСКА
# ─────────────────────────────────────────────────────────────────────────────

def _ensure_env() -> bool:
    """Создать .env из .env.example если ещё нет."""
    env = API_DIR / ".env"
    example = API_DIR / ".env.example"
    if not env.exists():
        if example.exists():
            import shutil as _sh
            _sh.copy(example, env)
            _warn(f".env не найден — скопирован из .env.example в {env}")
            _warn("Откройте social-api/.env и заполните SECRET_KEY и ключи API!")
        else:
            _err(".env и .env.example не найдены. Создайте social-api/.env вручную.")
            return False
    return True


def launch_all_docker() -> None:
    """docker compose up --build -d  (полный стек)"""
    _clear()
    print(_c(BOLD, "\n  🐳  ЗАПУСК ПОЛНОГО СТЕКА (Docker Compose)\n"))
    if not _has("docker"):
        _err("docker не установлен! https://docs.docker.com/get-docker/")
        _pause()
        return
    _ensure_env()
    print(_c(DIM, f"  Рабочая папка: {API_DIR}\n"))
    code = _run_live(["docker", "compose", "up", "--build", "-d"], cwd=API_DIR)
    print()
    if code == 0:
        _ok("Все сервисы запущены!")
        _info("API:     http://localhost:8000")
        _info("Swagger: http://localhost:8000/docs")
        _info("Nginx:   http://localhost:80")
        _info("Логи:    docker compose logs -f  (в папке social-api/)")
    else:
        _err(f"Ошибка запуска (код {code})")
    _pause()


def launch_db_redis() -> None:
    """Только db + redis."""
    _clear()
    print(_c(BOLD, "\n  🗄️  Запуск PostgreSQL + Redis\n"))
    if not _has("docker"):
        _err("docker не установлен!")
        _pause()
        return
    _ensure_env()
    code = _run_live(["docker", "compose", "up", "-d", "db", "redis"], cwd=API_DIR)
    print()
    if code == 0:
        _ok("PostgreSQL + Redis запущены")
        _info("Ожидание health check PostgreSQL…")
        time.sleep(3)
        _ok("Готово. Можно запускать API локально.")
    else:
        _err(f"Ошибка (код {code})")
    _pause()


def launch_api_local() -> None:
    """Alembic upgrade head + uvicorn (локально, без Docker для api)."""
    _clear()
    print(_c(BOLD, "\n  ⚡  Запуск FastAPI (локально, без Docker)\n"))
    _warn("Убедитесь, что PostgreSQL и Redis запущены (пункт 3 меню)!")
    print()
    py = "python3" if _has("python3") else "python"
    if not _has("uvicorn"):
        _info(f"Установка зависимостей…")
        _run_live([py, "-m", "pip", "install", "-e", "."], cwd=API_DIR)
    # alembic migrate
    print(_c(DIM, "  Применение миграций Alembic…"))
    _run_live(["alembic", "upgrade", "head"], cwd=API_DIR)
    print()
    _info("Запуск uvicorn на http://localhost:8000  (Ctrl+C для остановки)")
    print()
    _run_live(["uvicorn", "app.main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"], cwd=API_DIR)
    _pause()


def launch_celery_worker() -> None:
    """Celery worker."""
    _clear()
    print(_c(BOLD, "\n  ⚙️  Celery Worker\n"))
    _info("Ctrl+C для остановки")
    print()
    _run_live(
        ["celery", "-A", "app.tasks.celery_app", "worker",
         "--loglevel=info", "--concurrency=4"],
        cwd=API_DIR,
    )
    _pause()


def launch_celery_beat() -> None:
    """Celery Beat scheduler."""
    _clear()
    print(_c(BOLD, "\n  🕐  Celery Beat (Scheduler)\n"))
    _info("Ctrl+C для остановки")
    print()
    _run_live(
        ["celery", "-A", "app.tasks.celery_app", "beat", "--loglevel=info"],
        cwd=API_DIR,
    )
    _pause()


def launch_landing() -> None:
    """Serve index.html через http.server."""
    _clear()
    print(_c(BOLD, "\n  🌐  Landing Page (http.server)\n"))
    py = "python3" if _has("python3") else "python"
    port = 3000
    _info(f"Сервер запущен: http://localhost:{port}/index.html")
    _info("Ctrl+C для остановки")
    print()
    try:
        _run_live([py, "-m", "http.server", str(port), "--directory", str(ROOT)])
    except KeyboardInterrupt:
        pass
    _pause()


def run_tests() -> None:
    """pytest -v"""
    _clear()
    print(_c(BOLD, "\n  🧪  Запуск тестов (pytest)\n"))
    py = "python3" if _has("python3") else "python"
    if not _has("pytest"):
        _info("Установка pytest…")
        _run_live([py, "-m", "pip", "install", "pytest", "pytest-asyncio", "httpx"])
    print()
    code = _run_live(["pytest", "-v"], cwd=API_DIR)
    print()
    if code == 0:
        _ok("Все тесты прошли!")
    else:
        _warn(f"Некоторые тесты не прошли (код {code})")
    _pause()


def stop_all() -> None:
    """docker compose down"""
    _clear()
    print(_c(BOLD, "\n  🛑  Остановка всего стека\n"))
    if not _has("docker"):
        _err("docker не установлен!")
        _pause()
        return
    print(_c(YELLOW, "  Выберите режим остановки:"))
    print("   1. Остановить сервисы (данные сохранятся)")
    print("   2. Остановить + удалить тома данных (⚠️ данные будут удалены!)")
    print("   0. Отмена")
    choice = input("\n  Ваш выбор [0-2]: ").strip()
    if choice == "1":
        print()
        code = _run_live(["docker", "compose", "down"], cwd=API_DIR)
        print()
        if code == 0:
            _ok("Все сервисы остановлены. Данные сохранены.")
        else:
            _err(f"Ошибка (код {code})")
    elif choice == "2":
        confirm = input(_c(RED, "\n  ⚠️  Данные PostgreSQL и Redis будут удалены! Подтвердите (yes): ")).strip()
        if confirm.lower() == "yes":
            print()
            code = _run_live(["docker", "compose", "down", "-v"], cwd=API_DIR)
            print()
            if code == 0:
                _ok("Все сервисы остановлены. Тома данных удалены.")
            else:
                _err(f"Ошибка (код {code})")
        else:
            _info("Отменено.")
    _pause()


def show_status() -> None:
    """docker compose ps + health URLs."""
    _clear()
    print(_c(BOLD, "\n  📡  Статус сервисов\n"))
    if not _has("docker"):
        _err("docker не установлен!")
        _pause()
        return

    print(_c(DIM, "  Docker Compose ps:"))
    print(_c(DIM, "  " + _hr()))
    _run_live(["docker", "compose", "ps"], cwd=API_DIR)
    print(_c(DIM, "  " + _hr()))
    print()

    # Quick HTTP health checks
    try:
        import urllib.request
        checks = [
            ("FastAPI /health", "http://localhost:8000/health"),
            ("Nginx /api/health", "http://localhost:80/api/health"),
            ("Swagger /docs", "http://localhost:8000/docs"),
        ]
        for name, url in checks:
            try:
                with urllib.request.urlopen(url, timeout=2) as r:
                    _ok(f"{name:25s} → {r.status} OK  ({url})")
            except Exception as e:
                _err(f"{name:25s} → Недоступен  ({url})")
    except Exception:
        pass

    print()
    _info("Логи: docker compose logs -f api    (в папке social-api/)")
    _info("      docker compose logs -f worker")
    _pause()


def show_logs() -> None:
    """docker compose logs -f"""
    _clear()
    print(_c(BOLD, "\n  📋  Логи Docker Compose  (Ctrl+C для выхода)\n"))
    print("  Выберите сервис:")
    print("   1. api (FastAPI)")
    print("   2. worker (Celery Worker)")
    print("   3. beat (Celery Beat)")
    print("   4. nginx")
    print("   5. db (PostgreSQL)")
    print("   6. redis")
    print("   7. Все сервисы")
    choice = input("\n  Ваш выбор [1-7]: ").strip()
    svc_map = {"1": "api", "2": "worker", "3": "beat", "4": "nginx", "5": "db", "6": "redis"}
    print()
    if choice in svc_map:
        _run_live(["docker", "compose", "logs", "-f", "--tail=100", svc_map[choice]], cwd=API_DIR)
    elif choice == "7":
        _run_live(["docker", "compose", "logs", "-f", "--tail=50"], cwd=API_DIR)
    _pause()


def show_description() -> None:
    """Показать read-only описание проекта."""
    _clear()
    print(_c(BOLD, "\n  📖  ОПИСАНИЕ ПРОЕКТА (только чтение)\n"))
    print(_c(DIM, "  " + _hr("─", 64)))
    for line in READ_ONLY_DESCRIPTION:
        print(_c(CYAN, "  " + line))
    print(_c(DIM, "  " + _hr("─", 64)))
    print()
    _info("Это описание зашито в константу READ_ONLY_DESCRIPTION в start.py.")
    _info("Его невозможно изменить через меню — только через исходный код.")
    _pause()


def open_admin_html() -> None:
    """Открыть admin.html в браузере."""
    _clear()
    print(_c(BOLD, "\n  🛡️  Открытие Admin Panel (admin.html)\n"))
    import webbrowser
    path = ROOT / "admin.html"
    if not path.exists():
        _err("admin.html не найден!")
        _pause()
        return
    url = path.as_uri()
    _info(f"Открываем: {url}")
    webbrowser.open(url)
    _ok("Браузер открыт!")
    _pause()


def run_migrations() -> None:
    """alembic upgrade head"""
    _clear()
    print(_c(BOLD, "\n  🔄  Применение миграций Alembic\n"))
    if not _has("alembic"):
        py = "python3" if _has("python3") else "python"
        _info("alembic не найден, устанавливаем…")
        _run_live([py, "-m", "pip", "install", "alembic"], cwd=API_DIR)
    code = _run_live(["alembic", "upgrade", "head"], cwd=API_DIR)
    print()
    if code == 0:
        _ok("Миграции применены успешно!")
    else:
        _err(f"Ошибка миграций (код {code})")
    _pause()


# ─────────────────────────────────────────────────────────────────────────────
# ГЛАВНОЕ МЕНЮ
# ─────────────────────────────────────────────────────────────────────────────

MENU_ITEMS: list[tuple[str, str, object]] = [
    # (клавиша, описание, функция)
    ("1", "🐳  Запустить ВЕСЬ СТЕК  (docker compose up --build -d)",  launch_all_docker),
    ("2", "📡  Статус сервисов     (docker compose ps + health)",     show_status),
    ("3", "📋  Просмотр логов      (docker compose logs -f)",        show_logs),
    ("─", None, None),  # разделитель
    ("4", "🗄️  Запустить только DB + Redis  (docker)",               launch_db_redis),
    ("5", "⚡  Запустить API локально       (uvicorn --reload)",      launch_api_local),
    ("6", "⚙️  Запустить Celery Worker",                              launch_celery_worker),
    ("7", "🕐  Запустить Celery Beat",                                launch_celery_beat),
    ("8", "🔄  Применить миграции Alembic   (alembic upgrade head)", run_migrations),
    ("─", None, None),
    ("9", "🌐  Landing Page dev-сервер      (http://localhost:3000)", launch_landing),
    ("A", "🛡️  Открыть Admin Panel          (admin.html в браузере)", open_admin_html),
    ("─", None, None),
    ("T", "🧪  Запустить тесты              (pytest -v)",             run_tests),
    ("S", "🛑  Остановить всё               (docker compose down)",   stop_all),
    ("─", None, None),
    ("D", "📖  Описание проекта             (read-only)",             show_description),
    ("0", "🚪  Выход",                                                 None),
]


def _print_menu(deps: dict[str, bool]) -> None:
    _clear()
    _header()

    # Статус зависимостей
    print(_c(DIM, "  Зависимости: "), end="")
    for name, ok in deps.items():
        icon = _c(GREEN, "✔") if ok else _c(RED, "✘")
        print(f"  {icon} {name}", end="")
    print("\n")

    print(_c(DIM, "  " + _hr()))
    for key, label, _ in MENU_ITEMS:
        if key == "─":
            print(_c(DIM, "  " + _hr("·", 60)))
        else:
            key_str = _c(CYAN, f"[{key}]", bold=True)
            print(f"  {key_str}  {label}")
    print(_c(DIM, "  " + _hr()))
    print()


def main() -> None:
    deps = _check_deps()
    while True:
        _print_menu(deps)
        choice = input(_c(CYAN, "  Ваш выбор: ", bold=True)).strip().upper()
        print()

        if choice == "0":
            print(_c(GREEN, "\n  До свидания! 👋\n"))
            sys.exit(0)

        action_map = {key.upper(): fn for key, _, fn in MENU_ITEMS if key != "─" and fn is not None}
        fn = action_map.get(choice)
        if fn:
            fn()
        else:
            _err(f"Неизвестная команда: {choice!r}. Попробуйте снова.")
            time.sleep(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(_c(YELLOW, "\n\n  Прервано. До свидания! 👋\n"))
        sys.exit(0)
