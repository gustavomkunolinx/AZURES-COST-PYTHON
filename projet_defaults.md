# Default arq

- load venv: 
  - python -m venv .venv
  - source .venv/bin/activate
  - pip install --upgrade pip
  - pip install -r requirements.txt

- update reqs:  pip freeze > requirements.txt

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


## Integrate with vault

@Microsoft.KeyVault(VaultName=VAULT NAME";SecretName=tf-sp-clientId)
@Microsoft.KeyVault(VaultName=VAULT NAME";SecretName=tf-sp-clientSecret)
@Microsoft.KeyVault(VaultName=VAULT NAME";SecretName=tf-sp-subscriptionId)
@Microsoft.KeyVault(VaultName=VAULT NAME";SecretName=tf-sp-tenantId)
@Microsoft.KeyVault(VaultName=VAULT NAME";SecretName=sendgrid-email-api-token)


curl -X POST -H "Authorization: $TOKEN" https://func-cloud-azure-cost-report.azurewebsites.net/api/azure-cost-report

curl -X GET "https://func-cloud-azure-cost-report.azurewebsites.net/api/cost-report?code=${TOKEN}"



# TODO: Colocar descrição da subscription que está sendo analisada no e-mail
