"""
CLI for PDF Processing Pipeline.

Process PDF documents with text or LLM-based extraction.

Usage:
    # Process a single file
    python -m ai.features.pdf_processing.cli process document.pdf
    
    # Process a directory with text extraction
    python -m ai.features.pdf_processing.cli process ./pdfs/ --mode text
    
    # Process with LLM extraction  
    python -m ai.features.pdf_processing.cli process ./pdfs/ --mode llm
    
    # Process and store in database
    python -m ai.features.pdf_processing.cli process ./pdfs/ --project-id 123 --store
    
    # Generate report
    python -m ai.features.pdf_processing.cli report ./pdfs/ -o report.txt
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Optional, Sequence

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)


def cmd_process(args: argparse.Namespace) -> int:
    """Process PDF files."""
    from ai.features.pdf_processing import (
        PDFOrchestrator,
        ProcessingMode,
        TextExtractor,
        LLMExtractor,
    )
    
    input_path = Path(args.input)
    
    if not input_path.exists():
        logger.error(f"Input path not found: {input_path}")
        return 1
    
    # Map mode argument to ProcessingMode
    mode_map = {
        "text": ProcessingMode.TEXT_ONLY,
        "llm": ProcessingMode.LLM_ONLY,
        "hybrid": ProcessingMode.HYBRID,
        "auto": ProcessingMode.AUTO,
    }
    mode = mode_map.get(args.mode, ProcessingMode.TEXT_ONLY)
    
    # Create database session if storing
    db_session = None
    if args.store and args.project_id:
        try:
            from cg_rera_extractor.db.base import get_engine, get_session_local
            engine = get_engine()
            SessionLocal = get_session_local(engine)
            db_session = SessionLocal()
            logger.info("Database connection established")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            if not args.force:
                return 1
            logger.warning("Continuing without database storage")
    
    try:
        orchestrator = PDFOrchestrator(
            db_session=db_session,
            skip_processed=not args.reprocess
        )
        
        if input_path.is_file():
            # Single file processing
            logger.info(f"Processing single file: {input_path.name}")
            
            if args.store and args.project_id:
                result = orchestrator.process_and_store(
                    input_path,
                    project_id=args.project_id,
                    mode=mode
                )
            else:
                result = orchestrator.process_file(input_path, mode)
            
            # Print result
            print("\n" + "=" * 60)
            print(f"FILE: {result.filename}")
            print("=" * 60)
            print(f"Status:          {'SUCCESS' if result.success else 'FAILED'}")
            print(f"Document Type:   {result.document_type.value if result.document_type else 'Unknown'}")
            print(f"Confidence:      {result.document_type_confidence:.2%}" if result.document_type_confidence else "N/A")
            print(f"Pages:           {result.page_count}")
            print(f"Text Length:     {result.text_length:,} chars")
            print(f"Processing Time: {result.processing_time_ms}ms")
            
            if result.metadata:
                print("\nExtracted Metadata:")
                if result.metadata.approval_number:
                    print(f"  Approval Number: {result.metadata.approval_number}")
                if result.metadata.approval_date:
                    print(f"  Approval Date:   {result.metadata.approval_date}")
                if result.metadata.issuing_authority:
                    print(f"  Issuing Authority: {result.metadata.issuing_authority}")
                if result.metadata.dates:
                    print(f"  Dates Found:     {', '.join(result.metadata.dates[:5])}")
                if result.metadata.summary:
                    print(f"  Summary:         {result.metadata.summary[:200]}...")
            
            if result.warnings:
                print(f"\nWarnings: {', '.join(result.warnings)}")
            
            if result.error:
                print(f"\nError: {result.error}")
                return 1
            
        else:
            # Directory batch processing
            logger.info(f"Processing directory: {input_path}")
            
            if args.store and args.project_id:
                batch_result = orchestrator.process_directory_and_store(
                    input_path,
                    project_id=args.project_id,
                    mode=mode,
                    max_files=args.max_files
                )
            else:
                batch_result = orchestrator.process_directory(
                    input_path,
                    mode=mode,
                    max_files=args.max_files
                )
            
            # Print batch summary
            print("\n" + orchestrator.generate_report(batch_result))
            
            # Export JSON if requested
            if args.output_json:
                output_path = Path(args.output_json)
                orchestrator.export_results_json(batch_result, output_path)
                print(f"\nResults exported to: {output_path}")
            
            if batch_result.failed > 0:
                return 1
        
        return 0
        
    finally:
        if db_session:
            db_session.close()


def cmd_info(args: argparse.Namespace) -> int:
    """Show information about a PDF file."""
    from ai.features.pdf_processing import TextExtractor
    
    input_path = Path(args.input)
    
    if not input_path.exists():
        logger.error(f"File not found: {input_path}")
        return 1
    
    if not input_path.is_file():
        logger.error(f"Not a file: {input_path}")
        return 1
    
    extractor = TextExtractor(max_pages=5)  # Quick scan
    
    # Validate
    is_valid, error = extractor.validate_pdf(input_path)
    
    print(f"\nFile: {input_path.name}")
    print(f"Size: {input_path.stat().st_size:,} bytes")
    print(f"Valid PDF: {is_valid}")
    
    if not is_valid:
        print(f"Error: {error}")
        return 1
    
    # Quick extraction
    result = extractor.process(input_path)
    
    print(f"Pages: {result.page_count}")
    print(f"Text Length: {result.text_length:,} chars")
    print(f"Document Type: {result.document_type.value if result.document_type else 'Unknown'}")
    
    if args.preview and result.extracted_text:
        print(f"\nText Preview (first 500 chars):")
        print("-" * 40)
        print(result.extracted_text[:500])
        print("-" * 40)
    
    return 0


def cmd_stats(args: argparse.Namespace) -> int:
    """Show extraction statistics from database."""
    try:
        from cg_rera_extractor.db.base import get_engine, get_session_local
        from ai.features.pdf_processing import ExtractionStorage
        
        engine = get_engine()
        SessionLocal = get_session_local(engine)
        
        with SessionLocal() as session:
            storage = ExtractionStorage(session)
            stats = storage.get_extraction_stats(
                project_id=args.project_id if args.project_id else None
            )
        
        print("\nExtraction Statistics")
        print("=" * 40)
        print(f"Total Extractions: {stats['total_extractions']}")
        print(f"Successful:        {stats['successful']}")
        print(f"Failed:            {stats['failed']}")
        
        if stats['by_document_type']:
            print("\nBy Document Type:")
            for doc_type, count in sorted(stats['by_document_type'].items(), key=lambda x: -x[1]):
                print(f"  {doc_type}: {count}")
        
        if stats['by_processor']:
            print("\nBy Processor:")
            for processor, count in stats['by_processor'].items():
                print(f"  {processor}: {count}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        return 1


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="PDF Processing Pipeline CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process single PDF with text extraction
  python -m ai.features.pdf_processing.cli process document.pdf
  
  # Process directory with LLM extraction
  python -m ai.features.pdf_processing.cli process ./pdfs/ --mode llm
  
  # Process and store in database
  python -m ai.features.pdf_processing.cli process ./pdfs/ --project-id 123 --store
  
  # Show file info
  python -m ai.features.pdf_processing.cli info document.pdf --preview
  
  # Show database statistics
  python -m ai.features.pdf_processing.cli stats
"""
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Process command
    process_parser = subparsers.add_parser("process", help="Process PDF files")
    process_parser.add_argument(
        "input",
        help="Path to PDF file or directory"
    )
    process_parser.add_argument(
        "--mode", "-m",
        choices=["text", "llm", "hybrid", "auto"],
        default="text",
        help="Processing mode (default: text)"
    )
    process_parser.add_argument(
        "--project-id", "-p",
        type=int,
        help="Project ID for database storage"
    )
    process_parser.add_argument(
        "--store", "-s",
        action="store_true",
        help="Store results in database (requires --project-id)"
    )
    process_parser.add_argument(
        "--reprocess", "-r",
        action="store_true",
        help="Reprocess files even if already in database"
    )
    process_parser.add_argument(
        "--max-files",
        type=int,
        help="Maximum files to process"
    )
    process_parser.add_argument(
        "--output-json", "-o",
        help="Export results to JSON file"
    )
    process_parser.add_argument(
        "--force", "-f",
        action="store_true",
        help="Continue even if database connection fails"
    )
    process_parser.set_defaults(func=cmd_process)
    
    # Info command
    info_parser = subparsers.add_parser("info", help="Show PDF file information")
    info_parser.add_argument("input", help="Path to PDF file")
    info_parser.add_argument(
        "--preview",
        action="store_true",
        help="Show text preview"
    )
    info_parser.set_defaults(func=cmd_info)
    
    # Stats command
    stats_parser = subparsers.add_parser("stats", help="Show extraction statistics")
    stats_parser.add_argument(
        "--project-id", "-p",
        type=int,
        help="Filter by project ID"
    )
    stats_parser.set_defaults(func=cmd_stats)
    
    args = parser.parse_args(argv)
    
    if not args.command:
        parser.print_help()
        return 0
    
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
