import sys
import argparse
import urllib.request
import re
from typing import Dict, Set, List


def parse_args():
    parser = argparse.ArgumentParser(description="Инструмент визуализации графа зависимостей (Этап 3)")
    parser.add_argument("--package", "-p", required=True, help="Имя анализируемого пакета")
    parser.add_argument("--repo", "-r", required=True, help="URL репозитория или путь к файлу")
    parser.add_argument("--mode", "-m", choices=["real", "test"], default="real", help="Режим работы")
    parser.add_argument("--depth", "-d", type=int, default=10, help="Максимальная глубина анализа")
    return parser.parse_args()


def load_test_repo(file_path: str) -> Dict[str, List[str]]:
    """Загрузить тестовый граф из файла"""
    graph = {}
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue

                parts = line.split(':')
                if len(parts) == 2:
                    package = parts[0].strip()
                    deps_str = parts[1].strip()
                    deps = [d.strip() for d in deps_str.split(',') if d.strip()]
                    graph[package] = deps
                elif len(parts) == 1:
                    package = parts[0].strip()
                    graph[package] = []
    except Exception as e:
        raise Exception(f"Ошибка чтения файла: {e}")

    return graph


def get_cargo_toml(repo_url: str) -> str:
    """Получить Cargo.toml из репозитория"""
    if "github.com" in repo_url:
        repo_url = repo_url.rstrip("/")
        raw_url = repo_url.replace("github.com", "raw.githubusercontent.com")

        urls = [
            f"{raw_url}/main/Cargo.toml",
            f"{raw_url}/master/Cargo.toml",
        ]

        for url in urls:
            try:
                with urllib.request.urlopen(url) as response:
                    return response.read().decode('utf-8')
            except:
                continue

    raise Exception("Не удалось получить Cargo.toml")


def parse_dependencies(cargo_toml: str) -> List[str]:
    """Извлечь зависимости из Cargo.toml"""
    deps = []
    in_deps = False

    for line in cargo_toml.split('\n'):
        line = line.strip()

        if line == '[dependencies]':
            in_deps = True
            continue

        if line.startswith('[') and in_deps:
            break

        if in_deps and line and not line.startswith('#'):
            match = re.match(r'^([a-zA-Z0-9_-]+)\s*=', line)
            if match:
                deps.append(match.group(1))

    return deps


def get_dependencies_real(package: str, repo_url: str) -> List[str]:
    """Получить зависимости из реального репозитория"""
    cargo_content = get_cargo_toml(repo_url)
    return parse_dependencies(cargo_content)


class DependencyGraph:
    def __init__(self, mode: str, repo: str, max_depth: int):
        self.mode = mode
        self.repo = repo
        self.max_depth = max_depth
        self.graph: Dict[str, Set[str]] = {}
        self.visited: Set[str] = set()
        self.in_progress: Set[str] = set()
        self.cycles: List[List[str]] = []

        if mode == "test":
            self.test_graph = load_test_repo(repo)

    def get_deps(self, package: str) -> List[str]:
        """Получить зависимости пакета"""
        if self.mode == "test":
            return self.test_graph.get(package, [])
        else:
            try:
                return get_dependencies_real(package, self.repo)
            except:
                return []

    def dfs(self, package: str, depth: int, path: List[str]):
        """DFS для построения графа зависимостей"""
        if depth > self.max_depth:
            return

        if package in self.in_progress:
            # Обнаружен цикл
            cycle_start = path.index(package)
            cycle = path[cycle_start:] + [package]
            self.cycles.append(cycle)
            return

        if package in self.visited:
            return

        self.in_progress.add(package)
        path.append(package)

        # Получаем зависимости
        deps = self.get_deps(package)

        if package not in self.graph:
            self.graph[package] = set()

        for dep in deps:
            self.graph[package].add(dep)
            self.dfs(dep, depth + 1, path[:])

        path.pop()
        self.in_progress.remove(package)
        self.visited.add(package)

    def build(self, root_package: str):
        """Построить граф зависимостей"""
        self.dfs(root_package, 0, [])


def print_graph(graph: Dict[str, Set[str]], root: str):
    """Вывести граф зависимостей"""
    print(f"\nГраф зависимостей для '{root}':")
    print("=" * 50)

    if not graph:
        print("(нет зависимостей)")
        return

    for package in sorted(graph.keys()):
        deps = graph[package]
        if deps:
            print(f"{package}:")
            for dep in sorted(deps):
                print(f"  -> {dep}")
        else:
            print(f"{package}: (нет зависимостей)")


def main():
    try:
        args = parse_args()

        if args.depth < 0:
            raise ValueError("Глубина должна быть >= 0")

        print(f"Пакет: {args.package}")
        print(f"Режим: {args.mode}")
        print(f"Репозиторий: {args.repo}")
        print(f"Максимальная глубина: {args.depth}")

        # Строим граф
        dg = DependencyGraph(args.mode, args.repo, args.depth)
        dg.build(args.package)

        # Выводим результаты
        print_graph(dg.graph, args.package)

        # Выводим информацию о циклах
        if dg.cycles:
            print(f"\nОбнаружено циклических зависимостей: {len(dg.cycles)}")
            for i, cycle in enumerate(dg.cycles, 1):
                print(f"  Цикл {i}: {' -> '.join(cycle)}")
        else:
            print("\nЦиклические зависимости не обнаружены")

        print(f"\nВсего пакетов в графе: {len(dg.graph)}")
        total_deps = sum(len(deps) for deps in dg.graph.values())
        print(f"Всего связей: {total_deps}")

    except Exception as e:
        print(f"ОШИБКА: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()