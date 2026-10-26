# privacyseed-lgpd

Detect and anonymize personal data in Brazilian Portuguese text, mapped to the LGPD.

- Brazilian identifiers validated by check digit: CPF, CNPJ (including the alphanumeric format), PIS/PASEP/NIS, CNH, título de eleitor, payment cards (Luhn).
- E-mail, phone, CEP and dates of birth by pattern and context.
- Names and addresses with a local multilingual GLiNER2 model (`[ml]` extra).
- Sensitive data (LGPD art. 5, II), **experimental**: curated lexicon + zero-shot.

Demo: https://huggingface.co/spaces/fred-ai-lab/detector-lgpd · Built by [Privacy Seed](https://www.privacyseed.com.br/?utm_source=github&utm_medium=readme&utm_campaign=lgpd-detector)

## Install

```bash
pip install privacyseed-lgpd          # light core: identifiers, e-mail, phone, CEP, dates of birth
pip install 'privacyseed-lgpd[ml]'    # + names, addresses and sensitive data (PyTorch + model)
```

The light core depends only on PyYAML. Without `[ml]`, `Detector()` warns once and `Result.warnings` says what is not detected. For a smaller CPU-only install, get PyTorch first: `pip install torch --index-url https://download.pytorch.org/whl/cpu`. The model (~1 GB) downloads on first use.

## Usage

```python
from privacyseed_lgpd import Detector

det = Detector()
result = det.analyze("João Silva, CPF 123.456.789-09, tem diabetes.")

result.anonymized
# "[NOME], CPF [CPF], tem [DADO_SENSIVEL]."

result.entities    # anonymized findings: label, text, start/end offsets, score, source, LGPD category
result.flagged     # detected but kept in the text, with a warning (CNPJ by default)
result.discarded   # identifier-shaped values with an invalid check digit, kept for review
result.to_json()
```

Options:

```python
Detector(labels={"cpf", "email"})   # detect only these labels
Detector(anonymize={"cnpj"})        # anonymize CNPJs instead of flagging them
```

All numbers in this README and in the tests are fictional (random digits with valid check digits).

## Labels

| ID | Tag | LGPD | Detection | Default |
|---|---|---|---|---|
| `cpf` | `[CPF]` | art. 5, I | regex + check digit | anonymize |
| `cnpj` | `[CNPJ]` | art. 5, I | regex + check digit (numeric and alphanumeric) | **flag** |
| `pis` | `[PIS]` | art. 5, I | regex + check digit | anonymize |
| `cnh` | `[CNH]` | art. 5, I | regex + context + check digit | anonymize |
| `voter_id` | `[TITULO_ELEITOR]` | art. 5, I | regex + context + check digit | anonymize |
| `credit_card` | `[CARTAO]` | art. 5, I | regex + Luhn | anonymize |
| `email` | `[EMAIL]` | art. 5, I | regex | anonymize |
| `phone` | `[TELEFONE]` | art. 5, I | regex + valid area code | anonymize |
| `cep` | `[CEP]` | art. 5, I | regex + context | anonymize |
| `person_name` | `[NOME]` | art. 5, I | GLiNER2 | anonymize |
| `address` | `[ENDERECO]` | art. 5, I | GLiNER2 | anonymize |
| `birth_date` | `[DATA_NASCIMENTO]` | art. 5, I | regex + context; GLiNER2 | anonymize |
| `sensitive_data` | `[DADO_SENSIVEL]` | art. 5, II | lexicon + GLiNER2 zero-shot (experimental) | anonymize |

Sensitive data has 9 subcategories, one per item of art. 5, II (racial or ethnic origin, religious belief, political opinion, union membership, membership of a religious, philosophical or political organization, health, sex life, genetic, biometric). The anonymized text always says `[DADO_SENSIVEL]`, because a subcategory tag such as `[SAUDE]` would itself reveal sensitive information; the subcategory is in `entities` and the JSON.

A CNPJ identifies a legal entity and is in principle not personal data, so it is flagged, not anonymized. It can be personal data when it identifies an MEI or individual entrepreneur; the warning says so.

## Metrics

Golden set v0: 68 fictional, author-written sentences. Small and not independent: treat these numbers as a smoke test. A full PT-BR benchmark is coming. Exact span match (label + start + end).

| Label | Precision | Recall | F1 |
|---|---|---|---|
| `cpf`, `cnpj`, `pis`, `cnh`, `voter_id`, `credit_card`, `email`, `phone` | 1.00 | 1.00 | 1.00 |
| `birth_date` | 0.83 | 1.00 | 0.91 |
| `person_name` | 0.77 | 1.00 | 0.87 |
| `cep` | 1.00 | 0.60 | 0.75 |
| `address` | 0.33 | 0.60 | 0.43 |
| `sensitive_data` (9 subcategories, experimental) | 0.50–1.00 | 0.50–1.00 | 0.50–1.00 |

Per-label details, including each sensitive subcategory, are in [`METRICS.md`](METRICS.md). CI fails if any label's precision or recall drops below the recorded baseline.

## How it works

1. **Recognizers** find candidates independently: `regex` (light core), `gliner` and `sensitive` (`[ml]`).
2. The **resolver** keeps non-overlapping spans: a value that passed check-digit validation wins; then the longest span; then the highest score.
3. **Redaction** replaces each kept span by its tag, by offsets (repeated values are all replaced).

Inference is local only. The model is [`fastino/gliner2-privacy-filter-PII-multi`](https://huggingface.co/fastino/gliner2-privacy-filter-PII-multi) (Apache-2.0), pinned to a fixed revision; the library never uses the `gliner2` package's hosted inference client, so no text leaves your machine.

## Limitations

- No automated method finds 100% of personal data, and indirect information can allow re-identification. Always review the output.
- Sensitive data is experimental: explicit terms are caught better than inferences ("toma insulina todo dia").
- The model sometimes tags organizations or products as names, and address spans are often partial; a CEP inside an address is sometimes anonymized as part of `[ENDERECO]`.
- For título de eleitor from SP and MG, both check-digit variants found in practice are accepted, so no real number is missed.

## License

Apache-2.0. Model: `fastino/gliner2-privacy-filter-PII-multi` (Apache-2.0).

---

## Em português

**Anonimização automatizada de dados pessoais (LGPD).** A ferramenta detecta e remove dados pessoais por meio de modelos de IA e regras. Nenhum método automatizado identifica 100% dos dados, e a combinação de informações indiretas pode permitir a reidentificação. Se o resultado constitui dado anonimizado nos termos do art. 12 da LGPD depende de uma análise do contexto e dos meios razoavelmente disponíveis para reverter o processo. Revise sempre a saída. Esta ferramenta não constitui aconselhamento jurídico.

Precisa validar a anonimização dos seus dados? [Fale com a Privacy Seed](https://www.privacyseed.com.br/?utm_source=github&utm_medium=readme&utm_campaign=lgpd-detector).

## Privacidade desta demonstração

- **Uso recomendado:** a biblioteca roda localmente; nenhum texto sai do seu ambiente. Na demonstração, não cole dados reais.
- **O que a demonstração faz:** processa o texto apenas em memória para devolver o resultado. Não há registro, armazenamento, flagging ou analytics do texto, e a função não fica exposta como API.
- **Papel de agente:** se a LGPD se aplicar a esta demonstração gratuita (é discutível que haja tratamento com fins econômicos), a Privacy Seed atua como controladora do tratamento efêmero, por definir sua finalidade e seus meios, e o Hugging Face como operador (LGPD, art. 5º, VI e VII).
- **Base legal:** legítimo interesse (art. 7º, IX, e art. 10), com minimização garantida pelo aviso e pela ausência de persistência.
- **Transferência internacional:** a infraestrutura do Hugging Face fica fora do Brasil (art. 33). A [política de privacidade do Hugging Face](https://huggingface.co/privacy) (vigente desde 28/03/2023) informa que seus servidores ficam nos Estados Unidos e não indica um mecanismo específico de transferência internacional.
- **Limite:** os registros de infraestrutura do próprio Hugging Face (como IP e metadados de requisição) estão fora do controle da Privacy Seed.
