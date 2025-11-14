import sys
import argparse
import urllib.request
import re


def parse_args():
    parser = argparse.ArgumentParser(description="Инструмент визуализации графа зависимостей (Этап 2)")
    parser.add_argument("--package", "-p", required=True, help="Имя анализируемого пакета")
    parser.add_argument("--repo", "-r", required=True, help="URL репозитория")
    return parser.parse_args()


def get_cargo_toml(repo_url, package_name):
    """Получить содержимое Cargo.toml из репозитория"""
    # Преобразуем URL GitHub в raw URL
    if "github.com" in repo_url:
        repo_url = repo_url.rstrip("/")
        raw_url = repo_url.replace("github.com", "raw.githubusercontent.com")
        raw_url = raw_url.replace("/tree/", "/")

        # стратегия перебора возможных путей к файлу Cargo.toml
        urls = [
            f"{raw_url}/main/Cargo.toml",
            f"{raw_url}/master/Cargo.toml",
            f"{repo_url.replace('github.com', 'raw.githubusercontent.com')}/HEAD/Cargo.toml"
        ]

        # Отправляет HTTP GET запрос по указанному URL и возвращает объект ответа
        for url in urls:
            try:
                with urllib.request.urlopen(url) as response:
                    return response.read().decode('utf-8')
            except:
                continue

    raise Exception("Не удалось получить Cargo.toml из репозитория")


def parse_dependencies(cargo_toml_content):
    """Извлечь зависимости из Cargo.toml"""
    dependencies = [] # список где мы храним зависимости
    in_dependencies = False

    for line in cargo_toml_content.split('\n'):
        # убираем пробелы
        line = line.strip()

        # Начало секции [dependencies]
        if line == '[dependencies]':
            in_dependencies = True
            continue

        # Конец секции (новая секция)
        if line.startswith('[') and in_dependencies:
            break

        # Парсим зависимость
        if in_dependencies and line and not line.startswith('#'):
            # match ищет имена пакетов в файле Cargo.toml
            match = re.match(r'^([a-zA-Z0-9_-]+)\s*=', line)
            if match:
                # если match != None то извлекаем имя пакета
                dep_name = match.group(1)
                dependencies.append(dep_name)

    return dependencies


def main():
    try:
        args = parse_args()

        print(f"Получение зависимостей для пакета: {args.package}")
        print(f"Репозиторий: {args.repo}\n")

        # Получаем Cargo.toml
        cargo_content = get_cargo_toml(args.repo, args.package)

        # Парсим зависимости
        deps = parse_dependencies(cargo_content)

        # Выводим результат
        print(f"Прямые зависимости пакета '{args.package}':")
        if deps:
            for dep in deps:
                print(f"  - {dep}")
        else:
            print("  (нет зависимостей)")

        print(f"\nВсего зависимостей: {len(deps)}")

    except Exception as e:
        print(f"ОШИБКА: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()