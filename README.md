# Leitor de tela

Aperta um atalho, tira um print da janela em foco, extrai o texto com OCR (OpenAI `gpt-5-nano`) e lê em voz alta (edge-tts).

Funciona no Windows e no macOS.

## macOS

1. Instale o Python 3.10+ pelo [python.org](https://www.python.org/downloads/macos/) (o `python3` que vem no Mac é antigo demais).
2. Clone o repositório:
   ```bash
   git clone <url-do-repo> leitor-de-tela
   ```
3. Abra a pasta no Finder e dê dois cliques em `Iniciar.command`.
   Na primeira vez ele instala as dependências e pede a chave da OpenAI (fica salva no `.env`).
4. Libere as permissões para o **Terminal** em Ajustes do Sistema → Privacidade e Segurança:
   - **Gravação de Tela**: sem ela o print sai só com o papel de parede.
   - **Monitoramento de Entrada** e **Acessibilidade**: sem elas o atalho não funciona.

   Depois de liberar, feche o Terminal e abra o `Iniciar.command` de novo.

Uso: deixe o app em primeiro plano e aperte **Ctrl+Option+R**. **Ctrl+Option+Q** encerra.

Atualizar: `git pull` na pasta. Se o `requirements.txt` mudou, apague a pasta `.venv` e abra o `Iniciar.command` de novo.

## Windows

```bash
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
copy .env.example .env   # e coloque a OPENAI_API_KEY
.venv\Scripts\python screen_reader.py
```

Atalhos: **Ctrl+Alt+R** lê a janela em foco, **Ctrl+Alt+Q** encerra.

## Configuração

Tudo opcional, no `.env` (veja `.env.example`): modelo do OCR, voz, velocidade, atalhos, modo de captura (`window` ou `monitor`) e pastas de debug para salvar os prints e textos extraídos.
