# Metrics

Golden set v0: 68 fictional, author-written sentences. Small and not independent: treat these numbers as a smoke test. A full benchmark is coming.

Exact span match (label + start + end). Rows starting with `sensitive_data:` are **experimental**.

| Label | Precision | Recall | F1 | TP | FP | FN |
|---|---|---|---|---|---|---|
| `address` | 0.33 | 0.60 | 0.43 | 3 | 6 | 2 |
| `birth_date` | 0.83 | 1.00 | 0.91 | 5 | 1 | 0 |
| `cep` | 1.00 | 0.60 | 0.75 | 3 | 0 | 2 |
| `cnh` | 1.00 | 1.00 | 1.00 | 5 | 0 | 0 |
| `cnpj` | 1.00 | 1.00 | 1.00 | 5 | 0 | 0 |
| `cpf` | 1.00 | 1.00 | 1.00 | 5 | 0 | 0 |
| `credit_card` | 1.00 | 1.00 | 1.00 | 5 | 0 | 0 |
| `email` | 1.00 | 1.00 | 1.00 | 5 | 0 | 0 |
| `person_name` | 0.77 | 1.00 | 0.87 | 17 | 5 | 0 |
| `phone` | 1.00 | 1.00 | 1.00 | 7 | 0 | 0 |
| `pis` | 1.00 | 1.00 | 1.00 | 5 | 0 | 0 |
| `sensitive_data:biometric` | 1.00 | 1.00 | 1.00 | 2 | 0 | 0 |
| `sensitive_data:genetic` | 1.00 | 1.00 | 1.00 | 3 | 0 | 0 |
| `sensitive_data:health` | 1.00 | 0.83 | 0.91 | 5 | 0 | 1 |
| `sensitive_data:org_membership` | 1.00 | 1.00 | 1.00 | 2 | 0 | 0 |
| `sensitive_data:political_opinion` | 1.00 | 1.00 | 1.00 | 2 | 0 | 0 |
| `sensitive_data:racial_ethnic_origin` | 0.67 | 1.00 | 0.80 | 2 | 1 | 0 |
| `sensitive_data:religious_belief` | 1.00 | 0.67 | 0.80 | 2 | 0 | 1 |
| `sensitive_data:sex_life` | 1.00 | 1.00 | 1.00 | 2 | 0 | 0 |
| `sensitive_data:union_membership` | 0.50 | 0.50 | 0.50 | 1 | 1 | 1 |
| `voter_id` | 1.00 | 1.00 | 1.00 | 5 | 0 | 0 |
