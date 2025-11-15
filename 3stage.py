import sys
import argparse
import urllib.request
import json
from typing import Dict, Set, List


def parse_args():
    parser = argparse.ArgumentParser(description="Инструмент визуализации графа зависимостей (Этап 3)")
    parser.add_argument("--package", "-p", required=True, help="Имя анализируемого пакета")
    parser.add_argument("--repo", "-r", help="Путь к файлу тестового репозитория")
    parser.add_argument("--mode", "-m", choices=["real", "test"], default="real", help="Режим работы")
    parser.add_argument("--depth", "-d", type=int, default=10, help="Максимальная глубина анализа")
    return parser.parse_args()


def load_test_repo(file_path: str) -> Dict[str, List[str]]:
    """тестовый граф из файла"""
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


def get_dependencies_from_crates_io(package_name: str) -> List[str]:
    """Получить зависимости пакета через crates.io API"""
    versions_url = f"https://crates.io/api/v1/crates/{package_name}/versions"

    try:
        req = urllib.request.Request(versions_url)
        req.add_header('User-Agent', 'dependency-visualizer')

        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))

        versions = data.get('versions', [])
        if not versions:
            return []

        latest_version = versions[0]
        version_num = latest_version['num']

        deps_url = f"https://crates.io/api/v1/crates/{package_name}/{version_num}/dependencies"
        req_deps = urllib.request.Request(deps_url)
        req_deps.add_header('User-Agent', 'dependency-visualizer')

        with urllib.request.urlopen(req_deps, timeout=10) as response:
            deps_data = json.loads(response.read().decode('utf-8'))

        dependencies = []
        for dep in deps_data.get('dependencies', []):
            if dep.get('kind') == 'normal':
                dependencies.append(dep['crate_id'])

        return dependencies

    except urllib.error.HTTPError as e:
        if e.code == 404:
            return []
        else:
            raise Exception(f"HTTP ошибка для {package_name}: {e.code}")
    except Exception as e:
        print(f"Предупреждение: не удалось получить зависимости для {package_name}: {e}")
        return []


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
            return get_dependencies_from_crates_io(package)

    def dfs(self, package: str, depth: int, path: List[str]):
        """DFS для построения графа зависимостей"""
        if depth > self.max_depth:
            return

        if package in self.in_progress:
            cycle_start = path.index(package)
            cycle = path[cycle_start:] + [package]
            self.cycles.append(cycle)
            return

        if package in self.visited:
            return

        self.in_progress.add(package)
        path.append(package)

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

        if args.mode == "test" and not args.repo:
            raise ValueError("В тестовом режиме необходимо указать --repo с путем к файлу")

        print(f"Пакет: {args.package}")
        print(f"Режим: {args.mode}")
        if args.mode == "test":
            print(f"Тестовый репозиторий: {args.repo}")
        else:
            print(f"Источник: crates.io API")
        print(f"Максимальная глубина: {args.depth}")

        dg = DependencyGraph(args.mode, args.repo, args.depth)
        dg.build(args.package)

        print_graph(dg.graph, args.package)

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