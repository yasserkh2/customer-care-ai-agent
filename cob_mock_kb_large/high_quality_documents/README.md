High-quality document test set for retrieval evaluation.

Purpose:
- reduce repetitive synthetic wording from the very large mixed KB
- provide a much smaller document collection with stronger per-file coverage
- make service boundaries, intake requirements, and escalation rules clearer
- support isolated RAG testing with richer long-form grounding

Contents:
- `doc_0001_credentialing.md`
- `doc_0002_authorizations_benefits.md`
- `doc_0003_billing_denials.md`
- `doc_0004_medical_auditing.md`
- `doc_0005_customer_care.md`
- `doc_0006_digital_marketing.md`
- `doc_0007_financial_management.md`
- `doc_0008_communication_services.md`

Dataset notes:
- one document per canonical service from `very_large_mixed_kb/structured/services.csv`
- rewritten to be less repetitive and more realistic than the large synthetic source set
- intended for retrieval experiments where precision matters more than corpus size
