# Scripts Directory

This directory contains utility scripts for managing the shmuel-tech monorepo. All scripts follow consistent patterns for maintainability and developer experience.

## Established Patterns

### 1. Script Structure

All scripts should follow this basic structure:

```python
#!/usr/bin/env python3
"""
Brief description of what the script does.
More detailed explanation if needed.
"""

import argparse
import sys
from pathlib import Path
from typing import [relevant types]

# Import shared utilities
from .utils import load_project_env, check_fly_auth, run_command

# Load environment variables
load_project_env()

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Script description")
    # Add arguments...
    
    args = parser.parse_args()
    
    # Check Fly.io auth if needed
    if not check_fly_auth():
        print("❌ Not authenticated with Fly.io. Run 'fly auth login' first.")
        sys.exit(1)
    
    # Script logic...
    
    try:
        # Do work...
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n💥 Script failed with exception: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

### 2. Shared Utilities (`utils.py`)

Always use shared utilities for common operations:
- `load_project_env()` - Load environment variables from .env file
- `check_fly_auth()` - Verify Fly.io authentication
- `run_command(cmd, check=True, silent=False, input_data=None)` - Execute commands safely

### 3. Project Structure Assumptions

Scripts assume this project structure:
- Project root contains `services/` directory
- Each service has its own directory under `services/`
- Service directories may contain `.env` files
- Fly.io app names follow pattern: `shmuel-tech-{service_name}`

### 4. Command Line Interface

Use consistent CLI patterns:
- `--service` or `-s` for targeting specific services
- `--services-dir` for overriding services directory (default: `services`)
- `--dry-run` or `-n` for preview mode when applicable
- Descriptive help text for all arguments

### 5. Error Handling & Logging

- Use emoji prefixes for visual clarity: 🚀 ✅ ❌ ⚠️ 📋 🔧
- Print clear success/failure messages
- Handle exceptions gracefully with try/catch
- Exit with appropriate codes (0 for success, 1 for failure)
- Use `silent=True` for run_command() when output isn't needed

### 6. Entry Point Registration

Add new scripts to `pyproject.toml`:

```toml
[project.scripts]
script-name = "scripts.script_module:main"
```

### 7. Service Integration

For scripts that services should be able to call:

1. **Update `service_handler.py`**: Add Makefile targets that call the script
2. **Use relative paths**: `@cd ../.. && uv run script-name --service $(shell basename $(PWD))`
3. **Consistent naming**: Use kebab-case for script names and Makefile targets

### 8. Makefile Updates

When modifying service Makefiles, **always update the templates in `service_handler.py`**:

- **Go services**: Update `create_go_service_structure()` → `makefile_content`

This ensures new services get the same functionality as existing ones. The template is located at lines ~44-74 in the `create_go_service_structure()` function.

### 9. Type Hints

Use type hints for better code documentation:
- Import from `typing` module
- Annotate function parameters and return types
- Use `Optional[T]` for nullable values
- Use `List[T]`, `Dict[K, V]` for collections

## Examples

### Creating a New Script

1. Create `scripts/my_script.py` following the structure above
2. Add entry point to `pyproject.toml`
3. If services need to call it, update `service_handler.py` templates
4. Test with `uv run my-script --help`

### Testing Scripts

```bash
# Test individual service
uv run script-name --service dns-proxy --dry-run

# Test all services
uv run script-name --dry-run

# From service directory
cd services/dns-proxy && make target-name
```

## Available Scripts

- `deploy` - Deploy services to Fly.io
- `detect-changes` - Detect which services have changed
- `new-service` - Create new services
- `get-app-info` - Get Fly.io app information
- `sync-secrets` - Sync .env secrets to Fly.io

## Best Practices

1. **Keep it simple**: Focus on single responsibility
2. **Reuse utilities**: Don't reinvent common operations
3. **Consistent UI**: Follow established patterns for user experience
4. **Error resilient**: Handle edge cases gracefully
5. **Documentation**: Include docstrings and clear help text
6. **Testing**: Test with `--dry-run` when possible before making changes 