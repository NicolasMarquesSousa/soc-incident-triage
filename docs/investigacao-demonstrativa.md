# Investigação demonstrativa: login após falhas de autenticação

> Laboratório educacional com dados fictícios. Este documento descreve a amostra do repositório e a saída reproduzida da aplicação; não representa um incidente corporativo nem comprova comprometimento de conta.

## Objetivo

Demonstrar como passar de uma regra automática para uma decisão de triagem fundamentada, separando fatos observados, hipóteses e informações ainda necessárias.

## Reprodução

Na raiz de uma cópia do repositório, com Python 3.11 ou superior:

```powershell
$env:PYTHONPATH="src"
python -m unittest discover -s tests -v
python -m soc_triage.cli ingest data/sample_auth_events.csv --database demo.db
python -m soc_triage.cli alerts --database demo.db
```

Use um nome de banco ainda inexistente para reproduzir as contagens de inserção abaixo. Reprocessar a mesma amostra no mesmo banco não deve duplicar eventos.

Resultado da ingestão em banco novo:

```json
{
  "valid_events": 8,
  "invalid_events": 1,
  "inserted_events": 8,
  "detected_alerts": 4,
  "inserted_alerts": 4,
  "errors": ["Linha 10: timestamp inválido"]
}
```

A suíte disponível contém sete testes e foi executada com sucesso na preparação desta demonstração.

## Linha do tempo observada

Fonte: [CSV de demonstração](../data/sample_auth_events.csv). Os horários da amostra não informam fuso; não devem ser apresentados como UTC.

| Data | Horário | Usuário | IP de origem | Resultado |
|---|---|---|---|---|
| 22/09/2026 | 21:55 | ana | 203.0.113.10 | Falha |
| 22/09/2026 | 21:56 | ana | 203.0.113.10 | Falha |
| 22/09/2026 | 21:57 | ana | 203.0.113.10 | Falha |
| 22/09/2026 | 21:58 | ana | 203.0.113.10 | Falha |
| 22/09/2026 | 21:59 | ana | 203.0.113.10 | Falha |
| 22/09/2026 | 22:00 | ana | 203.0.113.10 | Sucesso |

O campo hostname dessas seis linhas é notebook-ana. O CSV, isoladamente, não esclarece o papel desse equipamento na arquitetura de autenticação.

## Alertas gerados

| Regra | Evidência | Severidade da regra | Pontuação |
|---|---|---|---|
| BRUTE_FORCE | Cinco falhas do mesmo IP em quatro minutos | Alta | 85 |
| SUCCESS_AFTER_FAILURES | Sucesso após cinco falhas do mesmo IP e usuário | Crítica | 95 |
| OFF_HOURS_LOGIN | Sucesso de ana às 22:00 | Média | 50 |
| OFF_HOURS_LOGIN | Sucesso de carla às 23:40 | Média | 50 |

O sucesso de bruno às 13:10 não gera alerta nesta amostra. Uma linha com timestamp inválido é rejeitada. A pontuação é uma heurística do projeto, não uma probabilidade de ataque.

## Hipóteses e verificações

| Hipótese | Por que considerar | O que falta verificar |
|---|---|---|
| Tentativa de adivinhação seguida de acesso indevido | Sequência concentrada de falhas e sucesso | Identidade do usuário, dispositivo, MFA e atividades da sessão |
| Usuário legítimo com dificuldade de acesso | Mesmo padrão pode resultar de senha digitada incorretamente | Confirmação com o usuário e histórico de acesso |
| Atividade de teste autorizada | O ambiente pode executar validações de autenticação | Janela de mudança, responsável e autorização |

Não há evidência suficiente para escolher uma dessas hipóteses como fato. Os IPs são de documentação: não há motivo para consultar reputação externa para concluir este exercício.

## Decisão de triagem

Priorizar a análise do sucesso após falhas, correlacionar a linha do tempo e manter o caso em investigação. A severidade da regra justifica atenção; ela não autoriza concluir invasão nem bloquear automaticamente uma conta.

Em uma operação real, consultar fontes autorizadas de identidade, MFA, VPN, endpoint e atividade posterior. Se o acesso indevido for confirmado, escalar conforme o procedimento da organização. Este projeto não executa contenção.

Para registrar o raciocínio, liste os alertas e use o ID correspondente à regra SUCCESS_AFTER_FAILURES. No banco novo desta reprodução, esse ID é 2:

```powershell
python -m soc_triage.cli status 2 investigating --analyst "Analista de laboratório" --note "Cinco falhas seguidas de sucesso; faltam contexto de MFA, dispositivo e confirmação do usuário. Comprometimento não confirmado." --database demo.db
python -m soc_triage.cli case 2 --database demo.db
```

Em bases já existentes, o ID pode ser diferente. Não marque o caso como resolvido apenas porque a regra foi acionada.

## Limitações e falsos positivos

- Login fora do horário pode ser trabalho autorizado; a regra usa horário fixo e não conhece escala, fuso ou exceções.
- Falhas agrupadas por IP podem reunir usuários distintos atrás de NAT; a regra de sucesso após falhas correlaciona IP e usuário.
- A amostra é pequena e sintética: não mede precisão, recall, desempenho em produção ou redução de tempo de investigação.
- O parser aceita datas ISO, mas não padroniza o fuso dos eventos. É necessário normalizar a origem antes de comparar horários; misturar datas com e sem fuso pode causar erro.
- Não há integração com SIEM, EDR ou provedor de identidade. Esses dados são verificações propostas, não funcionalidades implementadas.
- A aplicação não consulta ações posteriores ao login e não determina se a sessão foi maliciosa.

## Como apresentar em uma entrevista

Explique quais fatos acionaram a regra, duas hipóteses alternativas, quais fontes buscaria e por que não concluiu comprometimento. Reproduza os comandos e explique os limites do laboratório.
