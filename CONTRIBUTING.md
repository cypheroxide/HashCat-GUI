# Contributing to HashCat-GUI

First off, thank you for considering contributing to HashCat GUI! It's people like you who make HashCat GUI such a great tool.

## Code of Conduct

This project and everyone participating in it is governed by our [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code. Please report unacceptable behavior to [cypheroxide@cyberservices.com].

## Development Setup

### Prerequisites
- Python 3.8 or higher
- pip package manager
- Git
- HashCat

### Setting up your development environment
```bash
# Clone the repository
git clone https://github.com/cypheroxide/HashCat-GUI.git
cd HashCat-GUI

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate

# Install development dependencies
pip install -r requirements-dev.txt
```

## Coding Standards

### Python Style Guide
- Follow PEP 8 guidelines
- Use type hints for all function parameters and return values
- Maximum line length is 100 characters
- Use descriptive variable names
- Document classes and functions using docstrings

### Code Example
```python
from typing import List, Optional

def process_hash_file(
    file_path: str,
    hash_type: str,
    wordlist: Optional[str] = None
) -> List[str]:
    """Process a file containing hashes using specified parameters.

    Args:
        file_path: Path to the hash file
        hash_type: Type of hash (e.g., 'md5', 'sha256')
        wordlist: Optional path to wordlist file

    Returns:
        List of cracked hashes
    
    Raises:
        FileNotFoundError: If file_path doesn't exist
        ValueError: If hash_type is invalid
    """
    # Implementation
```

### Testing
- Write unit tests for all new features
- Maintain or improve test coverage
- Use pytest for testing
- Place tests in the `tests/` directory
- Name test files as `test_*.py`

## Pull Request Process

1. **Branch Naming**
- `feature/description` for new features
- `bugfix/description` for bug fixes
- `docs/description` for documentation changes

2. **Before Submitting**
- Update documentation if needed
- Add tests for new functionality
- Run the full test suite
- Update CHANGELOG.md
- Verify code style compliance

3. **PR Description Template**
```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Security update

## Tests
- [ ] New tests added
- [ ] Existing tests pass
```

## Issue Reporting Guidelines

### Bug Reports
Please include:
- HashCat-GUI version
- Operating system and version
- Steps to reproduce
- Expected vs actual behavior
- Relevant logs or screenshots

### Feature Requests
Please include:
- Clear use case description
- Proposed solution if any
- Alternative solutions considered
- Impact on existing functionality

## Testing Requirements

### Required Tests
- Unit tests for new functionality
- Integration tests for system interactions
- GUI tests for interface changes
- Performance tests for critical operations

### Running Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=HashCat-GUI tests/

# Run specific test file
pytest tests/test_specific.py
```

## Documentation Standards

### Code Documentation
- Use docstrings for modules, classes, and functions
- Include type hints
- Document exceptions and side effects
- Add inline comments for complex logic

### Project Documentation
- Keep README.md up to date
- Document new features in docs/
- Update API documentation
- Include examples for new functionality

### Documentation Example
```python
class HashProcessor:
    """Process and crack password hashes.

    This class handles the core functionality of processing hash files
    and interacting with hashcat for cracking passwords.

    Attributes:
        hash_type: The type of hash being processed
        wordlist: Path to the wordlist file
    """
```

## Security Considerations

### Code Security
- Never commit sensitive data
- Use secure random number generation
- Validate all user input
- Use proper file permissions
- Handle exceptions securely

### Testing Security
- Include security test cases
- Test input validation
- Verify file permission handling
- Test authentication if applicable

### Reporting Security Issues
- Do not create public issues for security vulnerabilities
- Email security concerns to [security@email.com]
- Use PGP encryption if possible
- Include detailed reproduction steps

## Getting Help

- Join our Discord server
- Check existing issues and discussions
- Review documentation
- Contact maintainers

Remember that this is an open-source project. Be patient with reviews and feedback, and thank you for contributing!

