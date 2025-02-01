# Security Policy

## Supported Versions

Use this section to tell people about which versions of your project are currently being supported with security updates.

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

We take all security vulnerabilities seriously. Please report any security issues by:

1. **DO NOT** create a GitHub issue for security vulnerabilities
2. Email security@hashbreaker.dev with details about the vulnerability
3. Allow up to 48 hours for a response
4. Do not disclose the vulnerability publicly until it has been addressed

We will:

1. Confirm receipt of your vulnerability report
2. Assess the impact and severity of the vulnerability
3. Develop and test a fix
4. Release a security update
5. Publicly disclose the vulnerability after the fix is released

### Security Recommendations

1. Always run HashBreaker with the minimum required privileges
2. Enable AppArmor/SELinux profiles when available
3. Keep the application and its dependencies updated
4. Monitor the application logs for suspicious activity
5. Use secure file permissions as documented in the installation guide

## Security Features

HashBreaker implements several security measures:

1. Process isolation
2. Secure file permissions
3. Temporary file cleanup
4. AppArmor/SELinux profiles
5. Input validation and sanitization
6. Secure hash handling
7. System resource limits

For more information about security features, please refer to our [documentation](docs/security.md).

