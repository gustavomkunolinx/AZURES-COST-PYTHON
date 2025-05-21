# Default arq

```bash
meu_projeto/
│
├── main.py                  # Arquivo principal que executa o projeto
├── requirements.txt         # Dependências do projeto (opcional)
│
├── utils/                   # Pasta para funções reutilizáveis
│   ├── __init__.py          # Torna a pasta um pacote Python
│   ├── arquivos.py          # Funções relacionadas a manipulação de arquivos
│   ├── calculos.py          # Funções matemáticas ou de processamento
│   └── validacoes.py        # Funções de validação de dados
│
└── data/                    # Pasta para armazenar dados (entrada/saída)
    └── exemplo.csv
```

## CODE

```python
from utils.calculos import soma

resultado = soma(5, 3)
print(resultado)
```
