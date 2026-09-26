#!/bin/bash
# Abre o leitor de tela no macOS. Na primeira vez instala o uv (que baixa o Python e as
# dependências sozinho) e pede a chave da OpenAI.
cd "$(dirname "$0")" || exit 1

fail() {
    echo "$1"
    read -r -p "Enter para fechar."
    exit 1
}

UV="$(command -v uv || echo "$HOME/.local/bin/uv")"
if [ ! -x "$UV" ]; then
    echo "Primeira execução: instalando o uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh || fail "Falhou a instalação do uv. Confira a internet e tente de novo."
fi

if [ ! -f .env ]; then
    read -r -s -p "Cole a chave da OpenAI e aperte Enter: " KEY
    echo
    printf 'OPENAI_API_KEY=%s\n' "$KEY" > .env
    chmod 600 .env
fi

echo "Preparando (na primeira vez baixa o Python e as dependências, leva uns minutos)..."
"$UV" sync --locked --quiet || fail "Falhou a instalação das dependências."

echo "Rodando. Ctrl+Option+R lê a janela em foco, Ctrl+Option+Q encerra."
"$UV" run --locked screen_reader.py
