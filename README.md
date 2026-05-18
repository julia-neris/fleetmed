# FleetMed MVP - Sistema de Medição de Custos de Frotas

Este é um MVP funcional para automatizar parte do processo de medição de custos de frotas.

## Funcionalidades incluídas

- Login simples por perfil:
  - Administrador
  - Fornecedor
  - Unidade
  - Medições/LVE
- Upload de medição em Excel
- Validação automática de campos obrigatórios
- Validação de CNPJ, razão social, unidade, placa, valor e tipo de cobrança
- Trava para arrendamento com divergência de valor contratual
- Consolidação em base única
- Tela para unidade validar SIM ou NÃO
- Justificativa obrigatória quando a unidade marcar NÃO
- Dashboard com total enviado, aceito, recusado e pendente
- Exportação da base consolidada em Excel

## Como rodar

1. Instale o Python 3.10 ou superior.

2. Abra o terminal dentro da pasta do projeto.

3. Instale as dependências:

```bash
pip install -r requirements.txt
```

4. Rode o sistema:

```bash
python app.py
```

5. Acesse no navegador:

```bash
http://127.0.0.1:5000
```

## Usuários de teste

### Administrador
Usuário: admin  
Senha: admin123

### Fornecedor
Usuário: fornecedor1  
Senha: forn123

### Unidade
Usuário: unidade1  
Senha: uni123

### Medições/LVE
Usuário: lve  
Senha: lve123

## Modelo de planilha de medição

A planilha de upload precisa conter as colunas abaixo:

- CNPJ
- RazaoSocial
- Unidade
- Placa
- TipoCobranca
- Valor
- Competencia
- Descricao

## Observações importantes

Este MVP usa arquivos CSV como base de dados para facilitar o teste inicial.
Para uso real em empresa, o ideal é evoluir para banco de dados PostgreSQL, autenticação corporativa, logs, permissões mais rígidas e integração com SAP/Power BI.
