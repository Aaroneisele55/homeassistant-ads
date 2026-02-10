# Contributing to ADS Custom

Thank you for your interest in contributing to the ADS Custom integration for Home Assistant!

## How to Contribute

### Reporting Issues

If you find a bug or have a feature request:

1. Check if the issue already exists in [GitHub Issues](https://github.com/Aaroneisele55/homeassistant-ads/issues)
2. If not, create a new issue with:
   - Clear description of the problem or feature
   - Steps to reproduce (for bugs)
   - Your Home Assistant version
   - Your PLC/TwinCAT version
   - Relevant YAML configuration (sanitized)
   - Log excerpts if applicable

### Submitting Pull Requests

1. **Fork the repository** and create a new branch for your changes
2. **Make your changes**:
   - Follow the existing code style
   - Add/update documentation as needed
   - Test your changes thoroughly
3. **Commit your changes** with clear, descriptive commit messages
4. **Submit a pull request** with:
   - Description of what changed and why
   - Reference to any related issues
   - Testing performed

### Development Setup

1. Clone your fork:
   ```bash
   git clone https://github.com/YOUR_USERNAME/homeassistant-ads.git
   cd homeassistant-ads
   ```

2. Make your changes in the `custom_components/ads_custom/` directory

3. Test locally by:
   - Copying to your Home Assistant `custom_components/` directory
   - Restarting Home Assistant
   - Checking logs for errors

### Code Guidelines

- Follow Python best practices and PEP 8 style guidelines
- Use type hints where possible
- Add docstrings to new functions and classes
- Keep changes focused and minimal
- Update documentation when adding features

### Documentation

When making changes that affect users:

- Update [docs/index.md](docs/index.md) for configuration changes
- Update [ENTITY_PARAMETERS.md](ENTITY_PARAMETERS.md) for parameter details
- Update [example_configuration.yaml](example_configuration.yaml) with examples
- Update [README.md](README.md) if needed

### Testing

Before submitting:

**Required steps:**

1. **Run the automated test suite:**
   ```bash
   pip install -r requirements_test.txt
   python -m pytest tests/ -v
   ```
2. Add new tests for any new or modified functionality (required for new or changed behavior; see `tests/` for examples)

**Additional manual testing (strongly recommended):**

- Test with a real PLC if possible
- Verify all entity types still work
- Check Home Assistant logs for errors
- Test both new installations and upgrades

## Questions?

- Check the [documentation](docs/index.md)
- Search existing [issues](https://github.com/Aaroneisele55/homeassistant-ads/issues)
- Ask on the [Home Assistant Community Forum](https://community.home-assistant.io/)

## Code of Conduct

Please be respectful and constructive in all interactions. We're all here to improve Home Assistant and help each other.

## License

By contributing, you agree that your contributions will be licensed under the Apache License 2.0.
