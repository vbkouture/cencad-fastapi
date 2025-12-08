"""
Script to export the OpenAPI schema to a JSON file.
Usage:
    python scripts/export_openapi.py
    python scripts/export_openapi.py --domain auth
"""

import argparse
import json
import sys
from pathlib import Path

from fastapi import FastAPI

# Add the project root to the python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.api.v1.routers import (
    analytics_router,
    assignments_router,
    auth_router,
    contact_forms_router,
    course_categories_router,
    courses_router,
    enrollments_router,
    job_roles_router,
    ping_router,
    schedules_router,
    submissions_router,
    users_router,
    vendors_router,
)
from app.main import create_app

DOMAIN_ROUTERS = {
    "analytics": analytics_router,
    "assignments": assignments_router,
    "auth": auth_router,
    "contact-forms": contact_forms_router,
    "courses": courses_router,
    "course-categories": course_categories_router,
    "job-roles": job_roles_router,
    "ping": ping_router,
    "submissions": submissions_router,
    "users": users_router,
    "vendors": vendors_router,
    "schedules": schedules_router,
    "enrollments": enrollments_router,
}


def export_openapi(domain: str | None = None) -> None:
    """Export the OpenAPI schema."""
    if domain:
        if domain not in DOMAIN_ROUTERS:
            print(
                f"Error: Domain '{domain}' not found. Available domains: {', '.join(DOMAIN_ROUTERS.keys())}"
            )
            sys.exit(1)

        # Create a minimal app for just this domain
        app = FastAPI(title=f"FastAPI - {domain}")
        app.include_router(DOMAIN_ROUTERS[domain], prefix="/api/v1")
        output_filename = f"openapi_{domain}.json"
    else:
        # Export full app
        app = create_app()
        output_filename = "openapi.json"

    # Get the schema
    openapi_data = app.openapi()

    # Define output path
    output_path = Path(output_filename)

    # Write to file
    with open(output_path, "w") as f:
        json.dump(openapi_data, f, indent=2)

    print(f"Successfully exported OpenAPI schema to {output_path.absolute()}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Export OpenAPI schema")
    parser.add_argument("--domain", help="Specific domain to export (e.g., auth, courses)")
    args = parser.parse_args()

    export_openapi(args.domain)
