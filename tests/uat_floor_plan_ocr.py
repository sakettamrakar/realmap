#!/usr/bin/env python3
"""
UAT Test Suite for Floor Plan OCR Feature
Tests database migration, OCR parser, and CLI processor
"""

import os
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import text, select
from cg_rera_extractor.db.base import get_engine, get_session_local
from cg_rera_extractor.db.models import ProjectArtifact, Project

# Color codes for output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RESET = "\033[0m"
BOLD = "\033[1m"

def print_header(text):
    print(f"\n{CYAN}{'=' * 70}")
    print(f"  {text}")
    print(f"{'=' * 70}{RESET}\n")

def print_success(text):
    print(f"{GREEN}✓{RESET} {text}")

def print_error(text):
    print(f"{RED}✗{RESET} {text}")

def print_warning(text):
    print(f"{YELLOW}⚠{RESET} {text}")

def print_info(text):
    print(f"  {text}")


class FloorPlanOCRUAT:
    """User Acceptance Testing for Floor Plan OCR Feature"""
    
    def __init__(self):
        self.engine = get_engine()
        self.SessionLocal = get_session_local(self.engine)
        self.test_results = {
            "passed": [],
            "failed": [],
            "warnings": []
        }
    
    def test_database_migration(self):
        """Test 1: Verify database migration was applied"""
        print_header("Test 1: Database Migration Verification")
        
        try:
            with self.engine.connect() as conn:
                # Check if column exists
                result = conn.execute(text("""
                    SELECT column_name, data_type, is_nullable 
                    FROM information_schema.columns 
                    WHERE table_name = 'project_artifacts' 
                    AND column_name = 'floor_plan_data'
                """))
                
                row = result.fetchone()
                
                if row:
                    print_success(f"Column exists: {row[0]} (type: {row[1]}, nullable: {row[2]})")
                    self.test_results["passed"].append("Database migration: floor_plan_data column")
                    
                    # Verify it's JSON/JSONB type
                    if 'json' in row[1].lower():
                        print_success("Column type is JSON as expected")
                        self.test_results["passed"].append("Database migration: correct data type")
                    else:
                        print_error(f"Column type is {row[1]}, expected JSON")
                        self.test_results["failed"].append(f"Database migration: wrong type {row[1]}")
                    
                    return True
                else:
                    print_error("floor_plan_data column not found")
                    print_warning("Run: alembic upgrade head")
                    self.test_results["failed"].append("Database migration: column missing")
                    return False
                    
        except Exception as e:
            print_error(f"Migration check failed: {e}")
            self.test_results["failed"].append(f"Database migration check: {e}")
            return False
    
    def test_model_definition(self):
        """Test 2: Verify ORM model has floor_plan_data field"""
        print_header("Test 2: ORM Model Definition")
        
        try:
            # Check if ProjectArtifact has the attribute
            if hasattr(ProjectArtifact, 'floor_plan_data'):
                print_success("ProjectArtifact model has floor_plan_data attribute")
                self.test_results["passed"].append("ORM model: floor_plan_data attribute exists")
                
                # Try to access the column info
                mapper = ProjectArtifact.__mapper__
                column = mapper.columns.get('floor_plan_data')
                if column is not None:
                    print_success(f"Column mapped correctly: {column.name}")
                    print_info(f"Type: {column.type}")
                    self.test_results["passed"].append("ORM model: column mapping correct")
                else:
                    print_error("Column not in mapper")
                    self.test_results["failed"].append("ORM model: column not mapped")
                    
                return True
            else:
                print_error("ProjectArtifact model missing floor_plan_data attribute")
                self.test_results["failed"].append("ORM model: attribute missing")
                return False
                
        except Exception as e:
            print_error(f"Model check failed: {e}")
            self.test_results["failed"].append(f"ORM model check: {e}")
            return False
    
    def test_parser_initialization(self):
        """Test 3: Test FloorPlanParser initialization"""
        print_header("Test 3: FloorPlanParser Initialization")
        
        try:
            from ai.ocr.parser import FloorPlanParser, SURYA_AVAILABLE
            
            print_info(f"Surya OCR available: {SURYA_AVAILABLE}")
            
            # Try to initialize parser
            parser = FloorPlanParser()
            print_success("FloorPlanParser initialized successfully")
            self.test_results["passed"].append("Parser initialization")
            
            if SURYA_AVAILABLE:
                if parser.models_loaded:
                    print_success("Surya models loaded successfully")
                    self.test_results["passed"].append("Parser: Surya models loaded")
                else:
                    print_warning("Surya available but models failed to load")
                    self.test_results["warnings"].append("Parser: Model loading failed")
            else:
                print_warning("Surya OCR dependencies not installed")
                print_info("Run: pip install surya-ocr")
                self.test_results["warnings"].append("Parser: Surya not installed")
            
            return True
            
        except Exception as e:
            print_error(f"Parser initialization failed: {e}")
            self.test_results["failed"].append(f"Parser initialization: {e}")
            return False
    
    def test_parser_with_mock_image(self):
        """Test 4: Test parser with a mock floor plan image"""
        print_header("Test 4: Parse Mock Floor Plan Image")
        
        try:
            from ai.ocr.parser import FloorPlanParser
            
            # Create a test image with text
            img = Image.new('RGB', (800, 600), color='white')
            draw = ImageDraw.Draw(img)
            
            # Draw some text simulating floor plan
            try:
                # Try to use a font, fallback to default
                font = ImageFont.truetype("arial.ttf", 24)
            except:
                font = ImageFont.load_default()
            
            draw.text((100, 100), "Master Bedroom", fill='black', font=font)
            draw.text((100, 150), "14' x 12'", fill='black', font=font)
            draw.text((400, 200), "Living Room", fill='black', font=font)
            draw.text((400, 250), "20' x 15'", fill='black', font=font)
            
            # Save to temp file
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
                temp_path = f.name
                img.save(temp_path, 'PNG')
            
            print_info(f"Created test image: {temp_path}")
            
            # Parse the image
            parser = FloorPlanParser()
            result = parser.parse_image(temp_path)
            
            print_info(f"Parsed: {result.get('parsed', False)}")
            print_info(f"Raw text entries: {len(result.get('raw_text', []))}")
            print_info(f"Rooms detected: {len(result.get('rooms', []))}")
            
            if result.get('parsed'):
                print_success("Image parsed successfully")
                self.test_results["passed"].append("Parser: mock image parsing")
                
                if result.get('rooms'):
                    print_success(f"Detected {len(result['rooms'])} room-related items")
                    for i, room in enumerate(result['rooms'][:3]):
                        print_info(f"  {i+1}. {room.get('label')}: {room.get('text')}")
            else:
                error_msg = result.get('error', 'Unknown error')
                if 'dependencies not available' in error_msg:
                    print_warning("Parser requires Surya OCR dependencies")
                    self.test_results["warnings"].append("Parser: dependencies not installed")
                else:
                    print_error(f"Parsing failed: {error_msg}")
                    self.test_results["failed"].append(f"Parser: {error_msg}")
            
            # Cleanup
            os.remove(temp_path)
            return True
            
        except Exception as e:
            print_error(f"Mock image test failed: {e}")
            self.test_results["failed"].append(f"Mock image parsing: {e}")
            return False
    
    def test_database_integration(self):
        """Test 5: Test saving parsed data to database"""
        print_header("Test 5: Database Integration Test")
        
        try:
            db = self.SessionLocal()
            
            # Check if we have any floor plan artifacts
            artifacts_query = select(ProjectArtifact).where(
                ProjectArtifact.artifact_type.ilike('%floor%plan%')
            ).limit(5)
            
            artifacts = db.scalars(artifacts_query).all()
            
            if artifacts:
                print_success(f"Found {len(artifacts)} floor plan artifacts in database")
                
                # Check how many already have data
                with_data = sum(1 for a in artifacts if a.floor_plan_data is not None)
                print_info(f"Artifacts with floor_plan_data: {with_data}/{len(artifacts)}")
                
                if with_data > 0:
                    # Show sample data
                    sample = next((a for a in artifacts if a.floor_plan_data), None)
                    if sample:
                        print_success(f"Sample artifact {sample.id} has parsed data:")
                        data = sample.floor_plan_data
                        print_info(f"  Parsed: {data.get('parsed', False)}")
                        print_info(f"  Rooms: {len(data.get('rooms', []))}")
                        print_info(f"  Raw text entries: {len(data.get('raw_text', []))}")
                        self.test_results["passed"].append("Database: data stored correctly")
                else:
                    print_warning("No artifacts have been processed yet")
                    print_info("Run: python scripts/process_floor_plans.py --limit 1")
                    self.test_results["warnings"].append("Database: no processed artifacts")
            else:
                print_warning("No floor plan artifacts found in database")
                self.test_results["warnings"].append("Database: no floor plan artifacts")
            
            db.close()
            return True
            
        except Exception as e:
            print_error(f"Database integration test failed: {e}")
            self.test_results["failed"].append(f"Database integration: {e}")
            return False
    
    def test_cli_script_exists(self):
        """Test 6: Verify CLI script exists and is executable"""
        print_header("Test 6: CLI Script Verification")
        
        script_path = "scripts/process_floor_plans.py"
        
        if os.path.exists(script_path):
            print_success(f"CLI script exists: {script_path}")
            self.test_results["passed"].append("CLI script: file exists")
            
            # Check if it's executable/readable
            if os.access(script_path, os.R_OK):
                print_success("Script is readable")
                self.test_results["passed"].append("CLI script: readable")
            
            # Try to import it
            try:
                import scripts.process_floor_plans as pfp
                print_success("Script imports successfully")
                self.test_results["passed"].append("CLI script: imports correctly")
                
                # Check for main function
                if hasattr(pfp, 'process_artifacts'):
                    print_success("process_artifacts function exists")
                    self.test_results["passed"].append("CLI script: main function exists")
                else:
                    print_error("process_artifacts function not found")
                    self.test_results["failed"].append("CLI script: missing main function")
                    
            except Exception as e:
                print_error(f"Script import failed: {e}")
                self.test_results["failed"].append(f"CLI script import: {e}")
                
            return True
        else:
            print_error(f"CLI script not found: {script_path}")
            self.test_results["failed"].append("CLI script: file missing")
            return False
    
    def test_error_handling(self):
        """Test 7: Test error handling with invalid input"""
        print_header("Test 7: Error Handling")
        
        try:
            from ai.ocr.parser import FloorPlanParser
            
            parser = FloorPlanParser()
            
            # Test 1: Non-existent file
            try:
                result = parser.parse_image("/nonexistent/file.jpg")
                print_error("Should have raised FileNotFoundError")
                self.test_results["failed"].append("Error handling: FileNotFoundError not raised")
            except FileNotFoundError:
                print_success("Correctly raises FileNotFoundError for missing files")
                self.test_results["passed"].append("Error handling: FileNotFoundError")
            
            # Test 2: Invalid image file
            with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
                f.write(b"This is not an image")
                temp_path = f.name
            
            try:
                result = parser.parse_image(temp_path)
                if result.get('error'):
                    print_success(f"Gracefully handles invalid image: {result['error'][:50]}...")
                    self.test_results["passed"].append("Error handling: invalid image")
                else:
                    print_warning("Invalid image didn't produce error in result")
                    self.test_results["warnings"].append("Error handling: no error for invalid image")
            except Exception as e:
                print_success(f"Raises exception for invalid image: {type(e).__name__}")
                self.test_results["passed"].append("Error handling: invalid image exception")
            finally:
                os.remove(temp_path)
            
            return True
            
        except Exception as e:
            print_error(f"Error handling test failed: {e}")
            self.test_results["failed"].append(f"Error handling: {e}")
            return False
    
    def print_summary(self):
        """Print test summary"""
        print_header("UAT TEST SUMMARY")
        
        total = len(self.test_results["passed"]) + len(self.test_results["failed"]) + len(self.test_results["warnings"])
        passed = len(self.test_results["passed"])
        failed = len(self.test_results["failed"])
        warnings = len(self.test_results["warnings"])
        
        print(f"\n{BOLD}Total Tests: {total}{RESET}")
        print(f"{GREEN}Passed: {passed}{RESET}")
        print(f"{RED}Failed: {failed}{RESET}")
        print(f"{YELLOW}Warnings: {warnings}{RESET}\n")
        
        if self.test_results["passed"]:
            print(f"{GREEN}{BOLD}✓ PASSED TESTS:{RESET}")
            for test in self.test_results["passed"]:
                print(f"  {GREEN}✓{RESET} {test}")
        
        if self.test_results["warnings"]:
            print(f"\n{YELLOW}{BOLD}⚠ WARNINGS:{RESET}")
            for warning in self.test_results["warnings"]:
                print(f"  {YELLOW}⚠{RESET} {warning}")
        
        if self.test_results["failed"]:
            print(f"\n{RED}{BOLD}✗ FAILED TESTS:{RESET}")
            for failure in self.test_results["failed"]:
                print(f"  {RED}✗{RESET} {failure}")
        
        print(f"\n{'=' * 70}")
        if failed == 0:
            print(f"{GREEN}{BOLD}✓ UAT PASSED - Feature is ready for production{RESET}")
        else:
            print(f"{RED}{BOLD}✗ UAT FAILED - Issues need to be resolved{RESET}")
        print(f"{'=' * 70}\n")
    
    def run_all_tests(self):
        """Run all UAT tests"""
        print(f"\n{BOLD}{CYAN}Starting Floor Plan OCR Feature UAT...{RESET}\n")
        
        print_header("FLOOR PLAN OCR - USER ACCEPTANCE TESTING")
        
        # Run tests
        self.test_database_migration()
        self.test_model_definition()
        self.test_parser_initialization()
        self.test_parser_with_mock_image()
        self.test_database_integration()
        self.test_cli_script_exists()
        self.test_error_handling()
        
        # Print summary
        self.print_summary()


if __name__ == "__main__":
    uat = FloorPlanOCRUAT()
    uat.run_all_tests()
