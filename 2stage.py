import sys
import argparse
import urllib.request
import json


def parse_args():
    parser = argparse.ArgumentParser(description="Инструмент визуализации графа зависимостей (Этап 2)")
    parser.add_argument("--package", "-p", required=True, help="Имя анализируемого пакета")
    return parser.parse_args()


def get_dependencies_from_crates_io(package_name):
    """Получить зависимости пакета через crates.io API"""
    versions_url = f"https://crates.io/api/v1/crates/{package_name}/versions"

    try:
        req = urllib.request.Request(versions_url)
        req.add_header('User-Agent', 'dependency-visualizer')

        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode('utf-8'))

        # Получаем последнюю версию пакета
        versions = data.get('versions', [])
        if not versions:
            return []

        # Берем первую версию (самая новая)
        latest_version = versions[0]
        version_num = latest_version['num']

        # Получаем зависимости конкретной версии
        deps_url = f"https://crates.io/api/v1/crates/{package_name}/{version_num}/dependencies"
        req_deps = urllib.request.Request(deps_url)
        req_deps.add_header('User-Agent', 'dependency-visualizer')

        with urllib.request.urlopen(req_deps) as response:
            deps_data = json.loads(response.read().decode('utf-8'))

        dependencies = []
        for dep in deps_data.get('dependencies', []):
            # Игнорируем dev-зависимости и build-зависимости
            if dep.get('kind') == 'normal':
                dependencies.append(dep['crate_id'])

        return dependencies

    except urllib.error.HTTPError as e:
        if e.code == 404:
            raise Exception(f"Пакет '{package_name}' не найден на crates.io")
        else:
            raise Exception(f"HTTP ошибка: {e.code}")
    except Exception as e:
        raise Exception(f"Ошибка при получении данных: {e}")


def main():
    try:
        args = parse_args()

        print(f"Получение зависимостей для пакета: {args.package}")
        print(f"Источник: crates.io API\n")

        # Получаем зависимости через API
        deps = get_dependencies_from_crates_io(args.package)

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