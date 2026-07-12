# Roadmap

## v1.0.0 — Foundation
- [x] Project scaffolding & architecture
- [x] Authentication & user management
- [x] Document upload & storage
- [x] Embedding pipeline (extract → chunk → embed → store)
- [x] RAG chat with conversation history
- [x] Knowledge base management
- [x] Dashboard & analytics
- [x] Testing (40+ tests, cross-user isolation)

## v1.1.0 — Knowledge Companion (Current Release)
- [x] Migrated default AI provider to Gemini (free tier)
- [x] Source citations — document name, page number, confidence score, expandable UI
- [x] Personality modes — Professional, Tutor, Friendly, Playful, opt-in Roast
- [x] Conversation history — rename, search, delete
- [x] Cross-document reasoning — source-labeled context, explicit synthesis instructions
- [x] Document intelligence — AI summaries, suggested questions
- [x] Related document recommendations (embedding similarity, no extra API calls)
- [x] Navigation shell, toast notifications, mobile-responsive UI polish
- [x] Testing (84 tests, cross-user isolation)

## v1.2.0 — Next
- [ ] Email notifications & password reset
- [ ] Pagination for documents, conversations, and knowledge bases
- [ ] Batch document upload
- [ ] Document search & filtering
- [ ] Usage analytics dashboard (time-series charts)
- [ ] Bump `langchain-google-genai` off the deprecated legacy Google SDK
- [ ] Remove or complete the unused Qdrant integration (currently dead code alongside ChromaDB)

## v1.3.0 — Medium Term
- [ ] Team/collaboration features (shared knowledge bases)
- [ ] Role-based access control (admin, editor, viewer)
- [ ] Webhook integrations (Slack, Zendesk, Intercom)
- [ ] Custom embedding models (Cohere, Hugging Face)
- [ ] Multi-language support

## v1.4.0 — Long Term
- [ ] Real-time chat widget embedding
- [ ] Feedback loop (thumbs up/down on answers)
- [ ] A/B testing for LLM prompts
- [ ] LLM-as-a-judge evaluation pipeline
- [ ] Content moderation & PII redaction
- [ ] CI/CD pipeline with GitHub Actions
- [ ] Performance benchmarking & load testing

## v2.0.0 — Vision
- [ ] Multi-tenant SaaS architecture
- [ ] Plugin/extension marketplace
- [ ] Custom training UI (fine-tune on your data)
- [ ] Analytics dashboard with charts and export
- [ ] OpenAI / Anthropic / Ollama provider switching
