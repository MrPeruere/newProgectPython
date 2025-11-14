# 1 этап
import sys
import os
import argparse
from urllib.parse import urlparse


def parse_args() -> argparse.Namespace:
    """Парсинг аргументов командной строки"""
    parser = argparse.ArgumentParser(
        description="Инструмент визуализации графа зависимостей (Этап 1)"
    )

    parser.add_argument(
        "--package", "-p",
        required=True,
        help="Имя анализируемого пакета (обязательно)"
    )

    parser.add_argument(
        "--repo", "-r",
        required=True,
        help="URL репозитория или путь к файлу тестового репозитория"
    )

    parser.add_argument(
        "--mode", "-m",
        choices=["real", "test"],
        default="real",
        help="Режим работы: real или test (по умолчанию: real)"
    )

    parser.add_argument(
        "--output", "-o",
        default="dependency_graph.png",
        help="Имя сгенерированного файла с изображением графа (по умолчанию: dependency_graph.png)"
    )

    parser.add_argument(
        "--ascii", "-a",
        action="store_true",
        help="Режим вывода зависимостей в формате ASCII-дерева"
    )

    parser.add_argument(
        "--depth", "-d",
        type=int,
        default=10,
        help="Максимальная глубина анализа зависимостей (по умолчанию: 10)"
    )

    return parser.parse_args()


def is_url(s: str) -> bool:
    """Проверка, является ли строка валидным URL"""
    try:
        parsed = urlparse(s)
        return parsed.scheme in ("http", "https") and bool(parsed.netloc)
    except Exception:
        return False


def validate_args(args: argparse.Namespace) -> None:
    """Валидация аргументов командной строки"""

    # Проверка package
    if not args.package or args.package.strip() == "":
        raise ValueError("Параметр --package обязателен и не может быть пустым")

    # Проверка mode
    if args.mode not in ("real", "test"):
        raise ValueError("Параметр --mode должен быть 'real' или 'test'")

    # Проверка repo в зависимости от режима
    if args.mode == "test":
        # В тестовом режиме repo должен быть путем к файлу
        if not args.repo:
            raise ValueError("В тестовом режиме (--mode test) параметр --repo должен указывать путь к файлу")
        if not os.path.exists(args.repo):
            raise FileNotFoundError(f"Файл репозитория не найден: {args.repo}")
        if not os.path.isfile(args.repo):
            raise ValueError(f"Ожидался путь к файлу, а не к каталогу: {args.repo}")
    else:
        # В реальном режиме repo должен быть URL
        if not args.repo:
            raise ValueError("Параметр --repo обязателен и должен быть URL-адресом репозитория в режиме 'real'")
        if not is_url(args.repo):
            raise ValueError("В режиме 'real' параметр --repo должен быть корректным URL (http/https)")

    # Проверка output
    if not args.output or args.output.strip() == "":
        raise ValueError("Параметр --output не может быть пустым")

    # Проверка depth
    if args.depth < 0:
        raise ValueError("Параметр --depth должен быть целым числом >= 0")


def main():
    try:
        args = parse_args()
        validate_args(args)

    except FileNotFoundError as e:
        print(f"ОШИБКА: {e}", file=sys.stderr)
        sys.exit(2)
    except ValueError as e:
        print(f"Неверные параметры: {e}", file=sys.stderr)
        sys.exit(3)
    except Exception as e:
        print(f"Неожиданная ошибка при разборе параметров: {e}", file=sys.stderr)
        sys.exit(4)

    kv = {
        "package": args.package,
        "repo": args.repo,
        "mode": args.mode,
        "output": args.output,
        "ascii": args.ascii,
        "depth": args.depth,
    }

    for k, v in kv.items():
        print(f"{k} = {v}")


if __name__ == '__main__':
    main()