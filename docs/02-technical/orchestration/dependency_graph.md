# 🔗 Dependency Graph

This document visualizes the dependencies between the various modules in the RealMap ecosystem.

## 🏛️ Module Dependency DAG

Key architectural layers and their directional dependencies:

```mermaid
graph TB
    subgraph CONFIG["Configuration"]
        CFG_LOADER["config/loader"]
        CFG_MODELS["config/models"]
    end
    
    subgraph BROWSER["Browser Automation"]
        SESSION["browser/session"]
        SEARCH["browser/search_flow"]
    end
    
    subgraph PARSING["Parsing Core"]
        RAW["parsing/raw_extractor"]
        MAP["parsing/mapper"]
        SCH["parsing/schema"]
    end
    
    subgraph DB["Database"]
        ORM["db/models"]
        LOADER["db/loader"]
    end
    
    subgraph PDFPROC["PDF Processing"]
        OCR["ocr/ocr_engine"]
        CONV["ocr/pdf_converter"]
        CLASS["extraction/classifier"]
        LLMEXT["extraction/llm_extractor"]
        MERGER["enrichment/data_merger"]
    end
    
    subgraph ENRICH["Enrichment"]
        GEO["geo/geocoder"]
        AMEN["amenities/scoring"]
    end
    
    subgraph ORCH["Orchestration"]
        RUN["runs/orchestrator"]
        PDFRUN["runs/pdf_processor"]
    end

    %% Flows
    CFG_MODELS --> CFG_LOADER
    
    CFG_LOADER --> RUN
    SESSION --> RUN
    SEARCH --> RUN
    
    SCH --> RAW
    RAW --> MAP
    MAP --> RUN
    
    ORM --> LOADER
    SCH --> LOADER
    LOADER --> RUN
    
    %% PDF Processing flows
    CONV --> OCR
    OCR --> CLASS
    CLASS --> LLMEXT
    LLMEXT --> MERGER
    MERGER --> PDFRUN
    PDFRUN --> LOADER
    
    ORM --> ENRICH
    GEO --> RUN
```

## 📦 File-Level Imports (Critical Path)

The following tree highlights the critical import chain for the main extraction runner:

```text
runs/orchestrator.py
├── config/loader.py
├── browser/session.py
├── listing/scraper.py
├── detail/fetcher.py
├── detail/preview_capture.py
├── parsing/raw_extractor.py
├── parsing/mapper.py
├── geo/
│   ├── geocoder.py
│   └── location_selector.py
├── quality/validation.py
└── db/loader.py
    └── db/models.py
```

### PDF Processing Import Chain

```text
runs/pdf_processor.py
├── ocr/
│   ├── pdf_converter.py
│   │   └── (pdf2image, PIL)
│   ├── ocr_engine.py
│   │   └── (pytesseract, easyocr)
│   └── text_cleaner.py
├── extraction/
│   ├── document_classifier.py
│   ├── llm_extractor.py
│   │   └── ai/llm/adapter.py
│   └── schemas/*.py
├── enrichment/
│   ├── conflict_resolver.py
│   └── data_merger.py
└── db/loader.py
```

## 🔄 Cyclic Dependency Risks

*   **Risk Area**: `db/loader.py` imports `quality/validation.py`. Ensure `quality` does not import `db` logic to avoid cycles.
*   **Risk Area**: `ai/main.py` imports `db/models.py`. Ensure core `db` models do not depend on `ai` components.
