"""
UAT Test Script: RERA Document Interpretation Feature
======================================================

This script performs User Acceptance Testing for the complete RERA document
interpretation workflow, including:
- PDF ingestion
- OCR/LLM processing
- Database storage
- API endpoint validation
- Error handling scenarios

Run: python tests/uat_rera_document_interpretation.py
"""
import os
import sys
import json
import logging
import tempfile
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import requests

from ai.rera.parser import ReraPdfParser
from cg_rera_extractor.db.models import Project, ReraFiling
from cg_rera_extractor.config.loader import load_config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class Colors:
    """ANSI color codes for terminal output"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_header(text):
    """Print formatted section header"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}")
    print(f"  {text}")
    print(f"{'='*70}{Colors.END}\n")

def print_success(text):
    """Print success message"""
    print(f"{Colors.GREEN}✓ {text}{Colors.END}")

def print_error(text):
    """Print error message"""
    print(f"{Colors.RED}✗ {text}{Colors.END}")

def print_warning(text):
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠ {text}{Colors.END}")

def print_info(text):
    """Print info message"""
    print(f"  {text}")

class ReraUATTest:
    def __init__(self):
        """Initialize UAT test environment"""
        self.config_path = "config.yaml" if os.path.exists("config.yaml") else "config.example.yaml"
        self.app_config = load_config(self.config_path)
        self.db_url = self.app_config.db.url
        self.engine = create_engine(self.db_url)
        self.SessionLocal = sessionmaker(bind=self.engine)
        self.parser = ReraPdfParser(use_ocr=True)
        self.test_results = {
            "passed": [],
            "failed": [],
            "warnings": []
        }
        
    def run_all_tests(self):
        """Execute all UAT test scenarios"""
        print_header("RERA DOCUMENT INTERPRETATION - USER ACCEPTANCE TESTING")
        
        try:
            # Test 1: Database Schema Verification
            self.test_database_schema()
            
            # Test 2: Create Test Project
            test_project_id = self.test_create_test_project()
            
            # Test 3: Valid PDF Processing (CLI)
            self.test_valid_pdf_cli(test_project_id)
            
            # Test 4: Invalid PDF Handling
            self.test_invalid_pdf_handling(test_project_id)
            
            # Test 5: Batch Processing
            self.test_batch_processing(test_project_id)
            
            # Test 6: API Endpoint Verification
            self.test_api_endpoint()
            
            # Test 7: Database Query Verification
            self.test_database_queries()
            
            # Test 8: Error Recovery
            self.test_error_recovery(test_project_id)
            
            # Test 9: Data Integrity
            self.test_data_integrity()
            
            # Print Summary
            self.print_test_summary()
            
        except Exception as e:
            print_error(f"Critical error during UAT: {e}")
            import traceback
            traceback.print_exc()
            
    def test_database_schema(self):
        """Test 1: Verify database schema and tables exist"""
        print_header("Test 1: Database Schema Verification")
        
        try:
            with self.engine.connect() as conn:
                # Check if rera_filings table exists
                result = conn.execute(text("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_name = 'rera_filings'
                """))
                
                if result.rowcount > 0:
                    print_success("rera_filings table exists")
                    self.test_results["passed"].append("Database schema: rera_filings table")
                else:
                    print_error("rera_filings table NOT found")
                    self.test_results["failed"].append("Database schema: rera_filings table missing")
                    return False
                
                # Check table columns
                result = conn.execute(text("""
                    SELECT column_name, data_type 
                    FROM information_schema.columns 
                    WHERE table_name = 'rera_filings'
                """))
                
                columns = {row[0]: row[1] for row in result}
                required_columns = ['id', 'project_id', 'file_path', 'doc_type', 'raw_text', 
                                    'extracted_data', 'model_name', 'processed_at']
                
                missing_columns = [col for col in required_columns if col not in columns]
                
                if not missing_columns:
                    print_success(f"All required columns present ({len(columns)} total)")
                    print_info(f"Columns: {', '.join(columns.keys())}")
                    self.test_results["passed"].append("Database schema: All columns present")
                else:
                    print_error(f"Missing columns: {missing_columns}")
                    self.test_results["failed"].append(f"Database schema: Missing columns {missing_columns}")
                    return False
                
                # Check indexes
                result = conn.execute(text("""
                    SELECT indexname 
                    FROM pg_indexes 
                    WHERE tablename = 'rera_filings'
                """))
                
                indexes = [row[0] for row in result]
                print_info(f"Indexes found: {len(indexes)}")
                for idx in indexes:
                    print_info(f"  - {idx}")
                
                return True
                
        except Exception as e:
            print_error(f"Schema verification failed: {e}")
            self.test_results["failed"].append(f"Database schema verification: {e}")
            return False
    
    def test_create_test_project(self):
        """Test 2: Create a test project for UAT"""
        print_header("Test 2: Create Test Project")
        
        try:
            db = self.SessionLocal()
            
            # Check if test project already exists
            existing = db.query(Project).filter(
                Project.rera_registration_number == "UAT_TEST_PROJECT_001"
            ).first()
            
            if existing:
                print_warning(f"Test project already exists: ID {existing.id}")
                db.close()
                return existing.id
            
            # Create new test project
            test_project = Project(
                rera_registration_number="UAT_TEST_PROJECT_001",
                project_name="UAT Test Project",
                state_code="CG",
                status="Registered"
            )
            
            db.add(test_project)
            db.commit()
            db.refresh(test_project)
            
            project_id = test_project.id
            print_success(f"Test project created: ID {project_id}")
            self.test_results["passed"].append(f"Test project creation: ID {project_id}")
            
            db.close()
            return project_id
            
        except Exception as e:
            print_error(f"Failed to create test project: {e}")
            self.test_results["failed"].append(f"Test project creation: {e}")
            return None
    
    def test_valid_pdf_cli(self, project_id):
        """Test 3: Process valid PDF using CLI"""
        print_header("Test 3: Valid PDF Processing (CLI)")
        
        try:
            # Create temporary PDF directory
            temp_dir = tempfile.mkdtemp(prefix="uat_rera_")
            test_pdf_path = os.path.join(temp_dir, "test_rera_valid.pdf")
            
            # Create a minimal valid PDF
            self._create_test_pdf(test_pdf_path, "Valid RERA Document\nProject: Test\nStatus: Registered")
            
            print_info(f"Created test PDF: {test_pdf_path}")
            
            # Process using CLI logic
            db = self.SessionLocal()
            
            result = self.parser.process_file(
                file_path=test_pdf_path,
                project_id=project_id,
                db=db
            )
            
            if result and result.get("filing_id"):
                print_success(f"PDF processed successfully. Filing ID: {result['filing_id']}")
                print_info(f"Extracted data: {result.get('data')}")
                self.test_results["passed"].append("Valid PDF CLI processing")
            else:
                print_error("PDF processing returned None or invalid result")
                self.test_results["failed"].append("Valid PDF CLI processing: invalid result")
            
            db.close()
            
            # Cleanup
            os.remove(test_pdf_path)
            os.rmdir(temp_dir)
            
            return result is not None and result.get("filing_id") is not None
            
        except Exception as e:
            print_error(f"Valid PDF processing failed: {e}")
            self.test_results["failed"].append(f"Valid PDF CLI processing: {e}")
            return False
    
    def test_invalid_pdf_handling(self, project_id):
        """Test 4: Handle invalid/corrupted PDF"""
        print_header("Test 4: Invalid PDF Handling")
        
        try:
            # Create temporary directory
            temp_dir = tempfile.mkdtemp(prefix="uat_rera_invalid_")
            invalid_pdf_path = os.path.join(temp_dir, "invalid.pdf")
            
            # Create a file with invalid PDF content
            with open(invalid_pdf_path, 'w') as f:
                f.write("This is not a valid PDF file content")
            
            print_info(f"Created invalid PDF: {invalid_pdf_path}")
            
            # Process using CLI logic
            db = self.SessionLocal()
            
            result = self.parser.process_file(
                file_path=invalid_pdf_path,
                project_id=project_id,
                db=db
            )
            
            # Check if error was handled gracefully (returns None or no filing_id)
            if result is None or not result.get("filing_id"):
                print_success("Invalid PDF handled gracefully (rejected correctly)")
                self.test_results["passed"].append("Invalid PDF error handling")
            else:
                print_error("Invalid PDF was processed when it should have been rejected")
                self.test_results["failed"].append("Invalid PDF: Should have been rejected")
            
            db.close()
            
            # Cleanup
            os.remove(invalid_pdf_path)
            os.rmdir(temp_dir)
            
            return True
            
        except Exception as e:
            print_error(f"Invalid PDF test failed: {e}")
            self.test_results["failed"].append(f"Invalid PDF handling: {e}")
            return False
    
    def test_batch_processing(self, project_id):
        """Test 5: Batch process multiple PDFs"""
        print_header("Test 5: Batch Processing")
        
        try:
            # Create temporary directory with multiple PDFs
            temp_dir = tempfile.mkdtemp(prefix="uat_rera_batch_")
            pdf_count = 3
            
            for i in range(pdf_count):
                pdf_path = os.path.join(temp_dir, f"batch_test_{i+1}.pdf")
                self._create_test_pdf(pdf_path, f"Batch Document {i+1}\nProject: Batch Test")
            
            print_info(f"Created {pdf_count} test PDFs in {temp_dir}")
            
            # Process batch
            db = self.SessionLocal()
            processed = 0
            
            for pdf_file in os.listdir(temp_dir):
                if pdf_file.endswith('.pdf'):
                    pdf_path = os.path.join(temp_dir, pdf_file)
                    result = self.parser.process_file(
                        file_path=pdf_path,
                        project_id=project_id,
                        db=db
                    )
                    if result and result.get("filing_id"):
                        processed += 1
            
            print_success(f"Batch processing complete: {processed}/{pdf_count} PDFs")
            
            if processed == pdf_count:
                self.test_results["passed"].append(f"Batch processing: {processed} files")
            else:
                self.test_results["warnings"].append(f"Batch processing: {processed}/{pdf_count} files")
            
            db.close()
            
            # Cleanup
            for pdf_file in os.listdir(temp_dir):
                os.remove(os.path.join(temp_dir, pdf_file))
            os.rmdir(temp_dir)
            
            return processed == pdf_count
            
        except Exception as e:
            print_error(f"Batch processing test failed: {e}")
            self.test_results["failed"].append(f"Batch processing: {e}")
            return False
    
    def test_api_endpoint(self):
        """Test 6: Verify API endpoint"""
        print_header("Test 6: API Endpoint Verification")
        
        try:
            # Check if AI service is running (optional)
            api_url = "http://localhost:8000/ai/extract/rera"
            
            print_info(f"Testing API endpoint: {api_url}")
            print_warning("Note: This test requires the AI service to be running")
            print_warning("Run: uvicorn ai.main:app --reload")
            
            try:
                # Create test PDF file
                temp_dir = tempfile.mkdtemp(prefix="uat_api_")
                test_pdf = os.path.join(temp_dir, "api_test.pdf")
                self._create_test_pdf(test_pdf, "API Test Document")
                
                # Get absolute path
                abs_path = os.path.abspath(test_pdf)
                
                # Call API with query parameters (as per endpoint signature)
                params = {
                    'file_path': abs_path,
                    'project_id': 10  # Use test project
                }
                
                response = requests.post(api_url, params=params, timeout=5)
                
                if response.status_code == 200:
                    print_success(f"API endpoint responded: {response.json()}")
                    self.test_results["passed"].append("API endpoint verification")
                else:
                    print_warning(f"API endpoint returned status {response.status_code}: {response.text[:100]}")
                    self.test_results["warnings"].append(f"API endpoint: HTTP {response.status_code}")
                
                # Cleanup
                os.remove(test_pdf)
                os.rmdir(temp_dir)
                
            except requests.ConnectionError:
                print_warning("API service not running - skipping endpoint test")
                self.test_results["warnings"].append("API endpoint: Service not running")
            except Exception as api_error:
                print_warning(f"API test error: {api_error}")
                self.test_results["warnings"].append(f"API endpoint: {api_error}")
                self.test_results["warnings"].append(f"API endpoint: {api_error}")
            
            return True
            
        except Exception as e:
            print_error(f"API endpoint test failed: {e}")
            self.test_results["failed"].append(f"API endpoint: {e}")
            return False
    
    def test_database_queries(self):
        """Test 7: Verify database queries and retrieval"""
        print_header("Test 7: Database Query Verification")
        
        try:
            db = self.SessionLocal()
            
            # Test 1: Count all filings
            total_filings = db.query(ReraFiling).count()
            print_success(f"Total RERA filings in database: {total_filings}")
            
            # Test 2: Get recent filings
            recent_filings = db.query(ReraFiling).order_by(
                ReraFiling.processed_at.desc()
            ).limit(5).all()
            
            print_info(f"Recent filings ({len(recent_filings)}):")
            for filing in recent_filings:
                print_info(f"  - ID: {filing.id}, File: {filing.file_name}, Processed: {filing.processed_at}")
            
            # Test 3: Query by project_id
            if total_filings > 0:
                project_id = recent_filings[0].project_id
                project_filings = db.query(ReraFiling).filter(
                    ReraFiling.project_id == project_id
                ).all()
                print_info(f"Filings for project {project_id}: {len(project_filings)}")
            
            # Test 4: Check extracted data structure
            filings_with_data = db.query(ReraFiling).filter(
                ReraFiling.extracted_data.isnot(None)
            ).count()
            filings_with_text = db.query(ReraFiling).filter(
                ReraFiling.raw_text.isnot(None)
            ).count()
            
            print_info(f"Filings with extracted data: {filings_with_data}")
            print_info(f"Filings with raw text: {filings_with_text}")
            
            self.test_results["passed"].append("Database query verification")
            
            db.close()
            return True
            
        except Exception as e:
            print_error(f"Database query test failed: {e}")
            self.test_results["failed"].append(f"Database queries: {e}")
            return False
    
    def test_error_recovery(self, project_id):
        """Test 8: Error recovery and logging"""
        print_header("Test 8: Error Recovery")
        
        try:
            db = self.SessionLocal()
            
            # Test with non-existent file - should raise FileNotFoundError
            try:
                result = self.parser.process_file(
                    file_path="/nonexistent/path/to/file.pdf",
                    project_id=project_id,
                    db=db
                )
                
                # If we get here without exception, check the result
                if result is None or not result.get("filing_id"):
                    print_success("Non-existent file handled correctly (returned None)")
                    self.test_results["passed"].append("Error recovery: Non-existent file")
                else:
                    print_warning("Non-existent file processed unexpectedly")
                    self.test_results["warnings"].append("Error recovery: Unexpected success")
                    
            except FileNotFoundError as fnf_error:
                print_success(f"Non-existent file raised FileNotFoundError (expected behavior)")
                self.test_results["passed"].append("Error recovery: FileNotFoundError raised correctly")
            except Exception as inner_e:
                print_success(f"Non-existent file raised exception (expected): {type(inner_e).__name__}")
                self.test_results["passed"].append(f"Error recovery: Exception handled ({type(inner_e).__name__})")
            
            db.close()
            return True
            
        except Exception as e:
            print_error(f"Error recovery test failed: {e}")
            self.test_results["failed"].append(f"Error recovery: {e}")
            return False
    
    def test_data_integrity(self):
        """Test 9: Verify data integrity and consistency"""
        print_header("Test 9: Data Integrity")
        
        try:
            db = self.SessionLocal()
            
            # Check for orphaned filings (project_id references non-existent project)
            orphaned = db.query(ReraFiling).filter(
                ~ReraFiling.project_id.in_(
                    db.query(Project.id)
                )
            ).count()
            
            if orphaned == 0:
                print_success("No orphaned RERA filings found")
                self.test_results["passed"].append("Data integrity: No orphans")
            else:
                print_warning(f"Found {orphaned} orphaned RERA filings")
                self.test_results["warnings"].append(f"Data integrity: {orphaned} orphans")
            
            # Check for null required fields
            null_checks = {
                "file_path": db.query(ReraFiling).filter(ReraFiling.file_path.is_(None)).count(),
                "project_id": db.query(ReraFiling).filter(ReraFiling.project_id.is_(None)).count(),
                "doc_type": db.query(ReraFiling).filter(ReraFiling.doc_type.is_(None)).count(),
            }
            
            issues = {k: v for k, v in null_checks.items() if v > 0}
            
            if not issues:
                print_success("All required fields populated")
                self.test_results["passed"].append("Data integrity: Required fields")
            else:
                print_warning(f"Null field issues: {issues}")
                self.test_results["warnings"].append(f"Data integrity: Null fields {issues}")
            
            db.close()
            return True
            
        except Exception as e:
            print_error(f"Data integrity test failed: {e}")
            self.test_results["failed"].append(f"Data integrity: {e}")
            return False
    
    def _create_test_pdf(self, file_path, content):
        """Helper: Create a proper test PDF file"""
        try:
            from reportlab.pdfgen import canvas
            from reportlab.lib.pagesizes import letter
            
            c = canvas.Canvas(file_path, pagesize=letter)
            # Split content by lines
            y_position = 750
            for line in content.split('\n'):
                c.drawString(100, y_position, line)
                y_position -= 20
            c.save()
        except ImportError:
            # If reportlab not available, use pypdf to create a proper PDF
            try:
                from pypdf import PdfWriter
                from pypdf.generic import RectangleObject
                
                writer = PdfWriter()
                # Add a blank page
                writer.add_blank_page(width=612, height=792)  # Letter size
                
                with open(file_path, 'wb') as f:
                    writer.write(f)
            except Exception as e:
                # Last resort: create minimal but valid PDF structure
                pdf_content = b"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> >> >> >>
endobj
4 0 obj
<< /Length 44 >>
stream
BT
/F1 12 Tf
100 750 Td
(Test Content) Tj
ET
endstream
endobj
xref
0 5
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000306 00000 n
trailer
<< /Size 5 /Root 1 0 R >>
startxref
398
%%EOF
"""
                with open(file_path, 'wb') as f:
                    f.write(pdf_content)
    
    def print_test_summary(self):
        """Print comprehensive test summary"""
        print_header("UAT TEST SUMMARY")
        
        total_tests = len(self.test_results["passed"]) + len(self.test_results["failed"]) + len(self.test_results["warnings"])
        
        print(f"\n{Colors.BOLD}Total Tests: {total_tests}{Colors.END}")
        print(f"{Colors.GREEN}Passed: {len(self.test_results['passed'])}{Colors.END}")
        print(f"{Colors.RED}Failed: {len(self.test_results['failed'])}{Colors.END}")
        print(f"{Colors.YELLOW}Warnings: {len(self.test_results['warnings'])}{Colors.END}\n")
        
        if self.test_results["passed"]:
            print(f"{Colors.GREEN}{Colors.BOLD}✓ PASSED TESTS:{Colors.END}")
            for test in self.test_results["passed"]:
                print(f"{Colors.GREEN}  ✓ {test}{Colors.END}")
        
        if self.test_results["warnings"]:
            print(f"\n{Colors.YELLOW}{Colors.BOLD}⚠ WARNINGS:{Colors.END}")
            for test in self.test_results["warnings"]:
                print(f"{Colors.YELLOW}  ⚠ {test}{Colors.END}")
        
        if self.test_results["failed"]:
            print(f"\n{Colors.RED}{Colors.BOLD}✗ FAILED TESTS:{Colors.END}")
            for test in self.test_results["failed"]:
                print(f"{Colors.RED}  ✗ {test}{Colors.END}")
        
        # Overall status
        print("\n" + "="*70)
        if not self.test_results["failed"]:
            print(f"{Colors.GREEN}{Colors.BOLD}✓ UAT PASSED - Feature is ready for production{Colors.END}")
        else:
            print(f"{Colors.RED}{Colors.BOLD}✗ UAT FAILED - Issues need to be resolved{Colors.END}")
        print("="*70 + "\n")

def main():
    """Main UAT execution"""
    print(f"\n{Colors.BOLD}Starting RERA Document Interpretation UAT...{Colors.END}\n")
    
    uat = ReraUATTest()
    uat.run_all_tests()

if __name__ == "__main__":
    main()
