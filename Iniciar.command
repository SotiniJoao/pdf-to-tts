#!/bin/bash
# Abre o leitor de tela no macOS. Na primeira vez cria o ambiente e pede a chave da OpenAI.
cd "$(dirname "$0")" || exit 1

if [ ! -d .venv ]; then
    PY=""
    for candidate in python3.13 python3.12 python3.11 python3.10 python3; do
        if command -v "$candidate" >/dev/null 2>&1 &&
            "$candidate" -c 'import sys; sys.exit(sys.version_info < (3, 10))' 2>/dev/null; then
            PY="$candidate"
            break
        fi
    done
    if [ -z "$PY" ]; then
        echo "Precisa do Python 3.10 ou mais novo. Instale pelo site python.org e abra de novo."
        read -r -p "Enter para fechar."
        exit 1
    fi
    echo "Primeira execução: instalando dependências (leva um minuto)..."
    "$PY" -m venv .venv && .venv/bin/pip install -q -r requirements.txt || {
        rm -rf .venv
        echo "Falhou a instalação."
        read -r -p "Enter para fechar."
        exit 1
    }
fi

if [ ! -f .env ]; then
    read -r -s -p "Cole a chave da OpenAI e aperte Enter: " KEY
    echo
    printf 'OPENAI_API_KEY=%s\n' "$KEY" > .env
    chmod 600 .env
fi

echo "Rodando. Ctrl+Option+R lê a janela em foco, Ctrl+Option+Q encerra."
.venv/bin/python screen_reader.py
