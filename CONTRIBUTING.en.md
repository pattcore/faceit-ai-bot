# Contributing Guide

Thank you for your interest in the project. I welcome all contributions.

## How to Contribute

### 1. Fork & Clone

```bash
git clone https://github.com/YOUR_USERNAME/faceit-ai-bot.git
cd faceit-ai-bot
```

### 2. Create a Branch

```bash
git checkout -b feature/your-awesome-feature
```

### 3. Make Your Changes

Make sure everything works:

```bash
# Check TypeScript
npm run type-check

# Lint your code
npm run lint

# Run tests
npm test
```

### 4. Commit Your Work

We use [Conventional Commits](https://www.conventionalcommits.org/) - it sounds fancy but it's simple:

```bash
git commit -m "feat: add new feature"
git commit -m "fix: fix that annoying bug"
git commit -m "docs: update readme"
```

**Commit types:**

- `feat` - new feature
- `fix` - bug fix
- `docs` - documentation
- `style` - code formatting
- `refactor` - code refactoring
- `test` - adding tests
- `chore` - updating dependencies

**Examples:**
```bash
git commit -m "feat: add player search"
git commit -m "fix: fix stats display"
git commit -m "docs: update installation guide"
```

### 5. Push & PR

```bash
git push origin feature/your-awesome-feature
```

Then create a Pull Request on GitHub!

## Code Style

### TypeScript/JavaScript

- Use ESLint and Prettier
- 2 spaces for indentation
- Semicolons are required

### Python

- Follow PEP 8
- 4 spaces for indentation
- Max line length: 88 characters (Black formatter)

### Commits

- Keep them short and sweet
- Write in present tense ("add feature" not "added feature")
- No AI/ML buzzwords - use simple terms like "analysis", "processing", "stats"

## Bug Reports

Found a bug? Create an issue with:

- Steps to reproduce
- What you expected
- What actually happened
- Version info
- Your environment (OS, browser, etc.)

## Feature Requests

Create an issue with the `enhancement` tag and describe:

- What problem it solves
- How you'd like it to work
- Any alternatives you considered

## License

By contributing, you agree that your contributions will be licensed under the [MIT License](LICENSE).

---

**[Russian version](CONTRIBUTING.md)**
