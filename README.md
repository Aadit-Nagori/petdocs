# PetVault 🐾

**One link. Every document. Any vet, anywhere.**

PetVault is a document management platform for pet owners. Upload your pet's vaccination records, medical history, prescriptions, and lab results — then generate a shareable link or QR code that any vet can scan to instantly access everything they need. No more digging through phone photos or paper folders at the vet's office.

---

## The Problem

Pet owners accumulate dozens of documents over a pet's lifetime — vaccine certificates, surgery notes, prescription records, allergy lists — scattered across emails, paper files, and camera rolls. When you switch vets, travel with your pet, or handle an emergency visit, pulling together the right documents is stressful and slow.

## How PetVault Solves It

1. **Upload** — Drag and drop documents (PDFs, photos, scans) into your pet's profile
2. **Auto-Extract** — OCR pipeline reads uploaded documents and extracts structured data: vaccine names, dates, vet clinics, next due dates
3. **Organize** — View a clean health timeline per pet, built automatically from extracted data
4. **Share** — Generate a unique link or QR code for any pet's records. Vets scan it and get instant read-only access
5. **Ask** — Natural language Q&A powered by RAG: *"Is Bella up to date on rabies?"* answered directly from your documents

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | Python, Django, Django REST Framework |
| **Database** | PostgreSQL (Supabase) |
| **File Storage** | Supabase Storage |
| **OCR** | EasyOCR + custom post-processing pipeline |
| **Search & RAG** | pgvector (Supabase), OpenAI Embeddings |
| **Frontend** | Django Templates (current) → Vite + React (planned) |
| **Auth** | Supabase Auth |

---

## Architecture

```
┌─────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Frontend  │────▶│ Django REST API  │────▶│    Supabase     │
│ (Templates) │     │                  │     │   PostgreSQL +  │
└─────────────┘     │  /api/pets/      │     │   Storage +     │
                    │  /api/documents/ │     │   pgvector      │
                    │  /api/share/     │     └─────────────────┘
                    │  /api/ask/       │
                    └────────┬─────────┘
                             │
                    ┌────────▼─────────┐
                    │  OCR Pipeline    │
                    │  EasyOCR → Parse │
                    │  → Structure →   │
                    │  Embed → Store   │
                    └──────────────────┘
```

---

## Current Status

- [x] Data models (Pet, Owner, Document, VetRecord)
- [x] Supabase PostgreSQL + Storage integration
- [x] REST API endpoints for CRUD operations
- [ ] Django template frontend for validation
- [ ] Document upload + OCR extraction pipeline
- [ ] Structured health timeline view
- [ ] Shareable link / QR code generation
- [ ] pgvector embeddings + RAG-based Q&A
- [ ] Vite + React frontend
- [ ] Deployment + live demo

---

## Getting Started

### Prerequisites
- Python 3.11+
- Supabase project (free tier works)

### Setup
```bash
git clone https://github.com/Aadit-Nagori/petvault.git
cd petvault
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Environment Variables
Create a `.env` file in the project root:
```
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_anon_key
SUPABASE_SERVICE_KEY=your_supabase_service_key
DJANGO_SECRET_KEY=your_django_secret
```

### Run
```bash
python manage.py migrate
python manage.py runserver
```

---

## Roadmap

**Phase 1 — Core Platform** *(Complete)*
Data layer, API, basic upload and retrieval

**Phase 2 — Intelligent Documents** *(In Progress)*
OCR pipeline for auto-extraction, structured health timeline

**Phase 3 — Share & Access**
QR code / link generation, read-only vet access portal

**Phase 4 — AI-Powered Q&A**
Document embeddings via pgvector, RAG-based natural language queries

**Phase 5 — Frontend & Deploy**
Vite + React frontend, production deployment

---

## Contributing

This is currently a solo project, but feedback and suggestions are welcome. Open an issue or reach out.

## License

MIT

---
