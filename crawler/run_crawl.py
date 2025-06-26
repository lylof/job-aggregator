import asyncio
import importlib
import pkgutil
import os
import sys

# Ajouter le dossier parent au path pour les imports
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from crawler.core.engine import SourceRunner

# Découverte dynamique des plugins sources
SOURCES_DIR = os.path.join(os.path.dirname(__file__), 'sources')

def discover_sources():
    sources = []
    for _, module_name, _ in pkgutil.iter_modules([SOURCES_DIR]):
        if module_name.startswith('__'):
            continue
        module = importlib.import_module(f'crawler.sources.{module_name}')
        for attr in dir(module):
            obj = getattr(module, attr)
            if isinstance(obj, type):
                # Hérite de AbstractSource ?
                bases = [base.__name__ for base in obj.__mro__]
                if 'AbstractSource' in bases and obj.__name__ != 'AbstractSource':
                    sources.append(obj())
    return sources

async def main():
    sources = discover_sources()
    print(f"[INFO] Sources découvertes: {[type(s).__name__ for s in sources]}")
    runners = [SourceRunner(source) for source in sources]
    await asyncio.gather(*(runner.crawl() for runner in runners))

if __name__ == '__main__':
    asyncio.run(main())
