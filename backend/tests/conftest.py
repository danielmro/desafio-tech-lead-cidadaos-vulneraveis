# Ajusta sys.path para permitir imports relativos ao projeto durante os testes
import os
import sys

# Garante que o diretório raiz do projeto esteja no sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
