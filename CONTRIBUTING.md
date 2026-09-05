# Contributing to Wildcard Prompt Studio

Thank you for your interest in contributing! This document outlines the development workflow and guidelines.

---

## Development Setup

### Prerequisites

- Python 3.10+
- Node.js 18+
- Docker & Docker Compose (optional but recommended)
- Git

### Clone & Setup

```bash
git clone https://github.com/mskiller/wildcard-prompt-studio.git
cd wildcard-prompt-studio

# Backend
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1   # Windows
# source venv/bin/activate    # Linux/Mac
pip install -r requirements.txt

# Frontend
cd ../frontend
npm install
```

---

## Branching Strategy

| Branch | Purpose |
|--------|---------|
| main | Stable release branch |
| eat/* | New features |
| ix/* | Bug fixes |
| docs/* | Documentation updates |
| chore/* | Maintenance tasks |

---

## Commit Convention

We use [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add ANIMA quality score injector
fix: resolve wildcard AST weight parsing edge case
docs: update API documentation for /ai/improve endpoint
chore: upgrade FastAPI to 0.115.0
test: add coverage for matrix sweep edge cases
```

---

## Pull Request Process

1. Fork the repository and create your branch from main
2. Make your changes with appropriate tests
3. Ensure all tests pass: `pytest backend/tests -v`
4. Update documentation if you changed behavior
5. Commit using the Conventional Commits format
6. Open a PR with a clear description of changes

---

## Code Style

### Python (Backend)

- Follow [PEP 8](https://peps.python.org/pep-0008/)
- Use type hints throughout
- Write docstrings for public functions
- Keep services focused on a single responsibility

### TypeScript (Frontend)

- Use TypeScript strict mode
- Prefer functional components with hooks
- Use Zustand stores for shared state — avoid prop drilling
- Keep components small and focused

---

## Running Tests

```bash
# Backend tests
pytest backend/tests -v

# Run specific test files
pytest backend/tests/test_krea2_optimizer.py -v
pytest backend/tests/test_wildcard_ast.py -v
pytest backend/tests/test_ai_providers.py -v
```

---

## Project Structure

```
wildcard-prompt-studio/
├── backend/
│   ├── main.py                  # FastAPI application entry point
│   ├── requirements.txt
│   ├── app/
│   │   ├── api/routers/         # Route handlers (ai, wildcards, prompts, ...)
│   │   ├── services/            # Business logic services
│   │   │   ├── ai/              # AI provider implementations
│   │   │   ├── wildcard_ast.py  # AST wildcard engine
│   │   │   ├── krea2_optimizer.py
│   │   │   ├── anima_optimizer.py
│   │   │   └── ...
│   │   ├── models/              # SQLAlchemy ORM models
│   │   └── schemas/             # Pydantic request/response schemas
│   └── tests/
├── frontend/
│   └── src/
│       ├── components/          # React UI components
│       ├── store/               # Zustand state stores
│       ├── utils/               # Utility functions
│       └── api.ts               # Backend API client
├── docs/                        # Documentation
├── docker-compose.yml
└── README.md
```

---

## Reporting Issues

Please open a GitHub Issue with:
- A clear title and description
- Steps to reproduce (if a bug)
- Expected vs actual behavior
- Environment details (OS, Python version, Node version)

---

## License

By contributing, you agree that your contributions will be licensed under the [MIT License](LICENSE).
