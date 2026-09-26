# Leitor de tela

Aperta um atalho, tira um print da janela em foco, extrai o texto com OCR (OpenAI `gpt-5-nano`) e lê em voz alta (edge-tts).

Funciona no Windows e no macOS. Dependências gerenciadas com [uv](https://docs.astral.sh/uv/).

## macOS (sem precisar instalar Python, Git nem VS Code)

Quem distribui gera o zip só com os arquivos do repositório (sem `.env`, `.venv` e debug):

```bash
git archive -o leitor-de-tela.zip HEAD
```

No Mac:

1. Descompacte o zip numa pasta.
2. Dê dois cliques em `Iniciar.command`. Por ser um arquivo baixado, o macOS bloqueia na primeira vez:
   vá em Ajustes do Sistema → Privacidade e Segurança, role até o aviso sobre o `Iniciar.command` e clique em
   **Abrir Mesmo Assim** (em versões antigas do macOS: botão direito no arquivo → **Abrir**). Só precisa fazer isso uma vez.
   Na primeira vez ele instala o uv, baixa o Python e as dependências e pede a chave da OpenAI (fica salva no `.env`).
3. Libere as permissões para o **Terminal** em Ajustes do Sistema → Privacidade e Segurança:
   - **Gravação de Tela**: sem ela o print sai só com o papel de parede.
   - **Monitoramento de Entrada** e **Acessibilidade**: sem elas o atalho não funciona.

   Depois de liberar, feche o Terminal e abra o `Iniciar.command` de novo.

Uso: deixe o app em primeiro plano e aperte **Control+Option+R**. **Control+Option+Q** encerra.
O Terminal mostra cada etapa (captura, texto extraído, fala) e os erros. Se faltar permissão, avisa ao abrir e abre a tela certa dos Ajustes.

Atualizar: descompacte o zip novo, abra a pasta nova, selecione tudo (Cmd+A), arraste para dentro da pasta antiga e escolha **Substituir**.
Não substitua a pasta inteira: a chave (`.env`) fica escondida na pasta antiga e se perderia. O `Iniciar.command` instala o que mudou.

## Windows

```bash
copy .env.example .env   # e coloque a OPENAI_API_KEY
uv run screen_reader.py
```

Atalhos: **Ctrl+Alt+R** lê a janela em foco, **Ctrl+Alt+Q** encerra.

## Configuração

Tudo opcional, no `.env` (veja `.env.example`): modelo do OCR, voz, velocidade, atalhos, modo de captura (`window` ou `monitor`) e pastas de debug para salvar os prints e textos extraídos.
