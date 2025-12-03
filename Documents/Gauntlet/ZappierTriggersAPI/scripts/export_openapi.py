#!/usr/bin/env python3
"""
Export OpenAPI Specification.

Generates a static openapi.json file for external documentation tools
and client SDK generation.

Usage:
    python scripts/export_openapi.py [--output FILE] [--format json|yaml]

Examples:
    python scripts/export_openapi.py
    python scripts/export_openapi.py --output docs/api/openapi.yaml --format yaml
"""

import argparse
import json
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "backend"))


def export_openapi(output_path: str | None = None, format: str = "json") -> None:
    """
    Export the OpenAPI specification to a file.

    Args:
        output_path: Output file path (default: docs/openapi.json or .yaml)
        format: Output format ('json' or 'yaml')
    """
    # Import the app to generate the schema
    from app.main import app

    # Get the OpenAPI schema
    openapi_schema = app.openapi()

    # Determine output path
    if output_path is None:
        docs_dir = project_root / "docs" / "api"
        docs_dir.mkdir(parents=True, exist_ok=True)
        extension = "yaml" if format == "yaml" else "json"
        output_path = docs_dir / f"openapi.{extension}"
    else:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write the schema
    if format == "yaml":
        try:
            import yaml

            with open(output_path, "w") as f:
                yaml.dump(
                    openapi_schema,
                    f,
                    default_flow_style=False,
                    allow_unicode=True,
                    sort_keys=False,
                )
        except ImportError:
            print("Error: PyYAML is required for YAML output. Install with: pip install pyyaml")
            sys.exit(1)
    else:
        with open(output_path, "w") as f:
            json.dump(openapi_schema, f, indent=2, ensure_ascii=False)

    print(f"✓ OpenAPI specification exported to: {output_path}")
    print(f"  Version: {openapi_schema.get('info', {}).get('version', 'unknown')}")
    print(f"  Title: {openapi_schema.get('info', {}).get('title', 'unknown')}")

    # Count endpoints
    paths = openapi_schema.get("paths", {})
    endpoint_count = sum(
        len([m for m in path_item.keys() if m in ("get", "post", "put", "patch", "delete")])
        for path_item in paths.values()
    )
    print(f"  Endpoints: {endpoint_count}")
    print(f"  Format: {format.upper()}")


def validate_openapi(schema_path: str) -> bool:
    """
    Validate an OpenAPI specification file.

    Args:
        schema_path: Path to the OpenAPI spec file

    Returns:
        True if valid, False otherwise
    """
    try:
        from openapi_spec_validator import validate_spec
        from openapi_spec_validator.readers import read_from_filename

        spec_dict, _ = read_from_filename(schema_path)
        validate_spec(spec_dict)
        print(f"✓ OpenAPI specification is valid: {schema_path}")
        return True
    except ImportError:
        print("Warning: openapi-spec-validator not installed. Skipping validation.")
        print("Install with: pip install openapi-spec-validator")
        return True
    except Exception as e:
        print(f"✗ OpenAPI specification is invalid: {e}")
        return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Export OpenAPI specification",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                              # Export to docs/api/openapi.json
  %(prog)s --format yaml                # Export as YAML
  %(prog)s --output api-spec.json       # Custom output path
  %(prog)s --validate docs/api/openapi.json  # Validate existing spec
        """,
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        help="Output file path",
    )
    parser.add_argument(
        "--format",
        "-f",
        choices=["json", "yaml"],
        default="json",
        help="Output format (default: json)",
    )
    parser.add_argument(
        "--validate",
        "-v",
        type=str,
        metavar="FILE",
        help="Validate an existing OpenAPI spec file",
    )

    args = parser.parse_args()

    if args.validate:
        success = validate_openapi(args.validate)
        sys.exit(0 if success else 1)
    else:
        export_openapi(args.output, args.format)


if __name__ == "__main__":
    main()
