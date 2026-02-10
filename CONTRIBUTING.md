# Contributing to AI-Counselling

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

## Code of Conduct

This project is committed to fostering an inclusive and welcoming environment. All contributors must adhere to our Code of Conduct.

## Getting Started

1. **Fork the Repository**
   ```bash
   git clone <your-forked-repo-url>
   cd ai-counselling
   ```

2. **Create a Feature Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Set Up Development Environment**
   ```bash
   npm install
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

4. **Make Your Changes**
   - Write clean, readable code
   - Follow existing code style
   - Add comments for complex logic

5. **Test Your Changes**
   - Run existing tests
   - Add new tests for new features
   - Verify no regressions

6. **Commit Your Changes**
   ```bash
   git commit -m "feat: description of your feature"
   ```
   Use conventional commits:
   - `feat:` for new features
   - `fix:` for bug fixes
   - `docs:` for documentation
   - `style:` for formatting
   - `refactor:` for code refactoring
   - `test:` for tests

7. **Push and Create Pull Request**
   ```bash
   git push origin feature/your-feature-name
   ```

## Pull Request Process

1. Update the README.md with details of changes if applicable
2. Ensure all tests pass
3. Request review from maintainers
4. Address any feedback
5. Maintainers will merge after approval

## Development Guidelines

### Frontend (Next.js/React)
- Use TypeScript for type safety
- Follow React best practices
- Use functional components and hooks
- Write tests for components
- Use Tailwind CSS for styling

### Backend (FastAPI/Python)
- Use type hints
- Write docstrings for functions
- Follow PEP 8 style guide
- Use async/await for I/O operations
- Write tests for endpoints

### Database
- Write migrations for schema changes
- Index frequently queried fields
- Write efficient queries
- Document complex queries

## Testing

Run tests before submitting:

```bash
# Frontend tests (if applicable)
npm test

# Backend tests (if applicable)
pytest
```

## Code Style

- **Frontend**: ESLint configuration is provided
  ```bash
  npm run lint
  ```

- **Backend**: Follow PEP 8, use type hints
  ```bash
  python -m pylint backend/
  ```

## Documentation

- Update README.md for user-facing changes
- Add docstrings to new functions/classes
- Update DEPLOYMENT.md for deployment-related changes
- Include comments for non-obvious code

## Reporting Issues

When reporting bugs, include:
- Clear description of the issue
- Steps to reproduce
- Expected vs actual behavior
- Environment details (OS, Node/Python version, etc.)
- Screenshots/logs if applicable

## Feature Requests

Feature requests are welcome! Please include:
- Clear description of the feature
- Use cases/motivation
- Proposed implementation (optional)
- Mockups/examples if applicable

## Performance Considerations

- Profile before optimizing
- Use CDN for static assets
- Optimize database queries
- Implement caching where appropriate
- Monitor resource usage

## Security

- Never commit secrets or credentials
- Use environment variables for sensitive data
- Report security issues privately to maintainers
- Keep dependencies up to date
- Use HTTPS in production

## License

By contributing, you agree that your contributions will be licensed under the same license as the project.

## Contact

For questions, please:
- Open a GitHub discussion
- Create an issue
- Contact the maintainers directly

Thank you for contributing! 🎉

