
import json
import sys
import os
from fastapi.openapi.utils import get_openapi
from app.main import app

# Ensure we're in the right directory
sys.path.insert(0, os.getcwd())

def generate_schedule_openapi():
    # Get the full OpenAPI spec
    full_openapi = app.openapi()
    
    # Filter for schedule-related paths
    schedule_paths = {}
    for path, methods in full_openapi['paths'].items():
        if 'schedule' in path:
            schedule_paths[path] = methods
            
    # Create the filtered OpenAPI spec
    schedule_openapi = {
        "openapi": full_openapi.get("openapi", "3.1.0"),
        "info": full_openapi.get("info", {}),
        "paths": schedule_paths,
        "components": full_openapi.get("components", {})
    }
    
    # Output to stdout
    print(json.dumps(schedule_openapi, indent=2))

if __name__ == "__main__":
    generate_schedule_openapi()
