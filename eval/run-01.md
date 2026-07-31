# Eval run 01

- Run at: 2026-07-31T09:31:58
- Model: gemini-3.1-flash-lite
- Gemini enabled: True
- Fallback enabled: False
- Golden set: `eval\golden-set.json`
- Document: day01
- Batch design: 4 x 5 fixed cases
- Result: 14/20

| Case | Type | Result | Page | Failed checks |
|---|---|---|---:|---|
| EVAL-01 | missing_information | PASS | 3 | - |
| EVAL-02 | ambiguous_context | FAIL | 4 | expected_terms_found |
| EVAL-03 | high_impact | PASS | 5 | - |
| EVAL-04 | out_of_scope | PASS | 6 | - |
| EVAL-05 | missing_information | PASS | 7 | - |
| EVAL-06 | normal | PASS | 8 | - |
| EVAL-07 | normal | PASS | 9 | - |
| EVAL-08 | ambiguous_context | PASS | 10 | - |
| EVAL-09 | normal | PASS | 11 | - |
| EVAL-10 | normal | PASS | 12 | - |
| EVAL-11 | high_impact | FAIL | 13 | provider_success, expected_terms_found, source_page_covered, review_evidence_grounded, review_generated_by_gemini |
| EVAL-12 | high_impact | FAIL | 14 | provider_success, expected_terms_found, source_page_covered, review_evidence_grounded, review_generated_by_gemini |
| EVAL-13 | normal | FAIL | 15 | provider_success, expected_terms_found, source_page_covered, review_evidence_grounded, review_generated_by_gemini |
| EVAL-14 | out_of_scope | FAIL | 16 | provider_success, expected_terms_found, source_page_covered, review_evidence_grounded, review_generated_by_gemini |
| EVAL-15 | normal | FAIL | 17 | provider_success, expected_terms_found, source_page_covered, review_evidence_grounded, review_generated_by_gemini |
| EVAL-16 | normal | PASS | 18 | - |
| EVAL-17 | normal | PASS | 19 | - |
| EVAL-18 | missing_information | PASS | 20 | - |
| EVAL-19 | high_impact | PASS | 21 | - |
| EVAL-20 | ambiguous_context | PASS | 22 | - |

Full inputs, expected criteria, observed outputs, and all failures are stored in `eval/run-01.json`.