# PDF Renaming Tool - Fix Plan

## Executive Summary

This plan addresses identified issues in the PDF Renaming Tool, focusing on critical bugs, deprecation warnings, performance improvements, and code quality enhancements. The fixes are organized by priority and include specific implementation steps, test updates, and validation criteria.

## Issues Identified

### Critical / High Priority
1. **PyPDF2 Deprecation** - PyPDF2 is deprecated; migration to `pypdf` required for security and maintenance
2. **Type Mismatch Bug** - `TitleNamingStrategy.generate()` may receive `None` for `title_candidate` despite `can_handle()` check (line 63 in `naming/title.py`)
3. **Duplicate PDF Reads** - Pipeline opens PDF twice (once for text extraction, once for title extraction), doubling I/O overhead
4. **Language Detection Return Type** - `LangdetectDetector.detect()` returns `Any` from `langdetect.detect`, violating type contract

### Medium Priority
5. **Linting Issues** - 12 ruff violations (import sorting, unused imports, needless bool, duplicate value)
6. **Mypy Errors** - Missing library stubs for nltk/langdetect, type mismatches
7. **Error Handling** - Some edge cases in PDF extraction may not be properly logged
8. **Collision Handling** - Potential edge case with extremely high collision counts (impractical but theoretically unbounded)

### Low Priority
9. **Code Style** - Inconsistent import ordering, minor style issues
10. **Documentation** - Some functions lack detailed docstrings
11. **Test Coverage** - Integration tests could be expanded with more edge cases

## Priority Order for Implementation

| Phase | Issue(s) | Estimated Effort | Risk |
|-------|----------|------------------|------|
| 1 | Fix type mismatch bug (#2) | Low | Low |
| 2 | Migrate PyPDF2 to pypdf (#1) | Medium | Medium |
| 3 | Fix linting issues (#5) | Low | Low |
| 4 | Fix mypy errors (#6) | Low | Low |
| 5 | Eliminate duplicate PDF reads (#3) | Medium | Medium |
| 6 | Improve language detection (#4) | Low | Low |
| 7 | Enhance error handling (#7) | Low | Low |
| 8 | Minor improvements (#9-11) | Low | Low |

## Step-by-Step Implementation

### Phase 1: Fix Type Mismatch Bug (Critical)

**Location**: `src/pdf_renamer/naming/title.py:63`

**Issue**: The `generate()` method calls `self._slugifier.sanitize(title, context.language)` where `title` is typed as `str | None`. Although `can_handle()` ensures `title_candidate` is not None, the type system doesn't narrow the type.

**Fix**:
1. Add a type guard assertion or cast after `can_handle()` check
2. Update method signature to use `assert` or explicit type narrowing

**Code Changes**:
```python
def generate(self, context: ProcessingContext) -> NamingResult | None:
    if not self.can_handle(context):
        return None

    # After can_handle() returns True, title_candidate is guaranteed to be str
    title = context.title_candidate
    assert title is not None  # Type guard for type checker
    
    slug = self._slugifier.sanitize(title, context.language)
    return NamingResult(name=slug, strategy_used="title")
```

**Test Updates**:
- Add test case where `title_candidate` is `None` but `can_handle()` returns `False`
- Add test case where `title_candidate` is a valid string
- Run existing tests to ensure no regression

**Validation**:
- Run `pytest tests/unit/test_naming.py -v`
- Run `mypy src/pdf_renamer/naming/title.py` to verify type safety

### Phase 2: Migrate PyPDF2 to pypdf (Critical)

**Location**: `src/pdf_renamer/extraction/pdf.py:8` and `src/pdf_renamer/processing/pipeline.py:128`

**Issue**: PyPDF2 is deprecated, causing deprecation warnings and potential future compatibility issues.

**Fix**:
1. Update dependency in `pyproject.toml`: replace `pypdf2>=3.0.1` with `pypdf>=4.0.0`
2. Update import statements from `from PyPDF2 import PdfReader` to `from pypdf import PdfReader`
3. Verify API compatibility (PdfReader API is largely compatible)

**Code Changes**:
```python
# In pyproject.toml
dependencies = [
    "langdetect>=1.0.9",
    "nltk>=3.9.4",
    "pypdf>=4.0.0",  # Changed from pypdf2
    "tqdm>=4.67.3",
]

# In extraction/pdf.py
from pypdf import PdfReader

# In processing/pipeline.py
from pypdf import PdfReader
```

**Test Updates**:
- Update any test imports if they use PyPDF2
- Run integration tests with real PDFs to ensure extraction works identically

**Validation**:
- Run `pytest tests/unit/test_extractor.py -v`
- Run `pytest tests/unit/test_processing.py -v`
- Verify no deprecation warnings in test output

### Phase 3: Fix Linting Issues (Medium)

**Location**: Multiple files across `src/`

**Issues**:
- I001: Unsorted imports (7 occurrences)
- F401: Unused imports (3 occurrences)
- SIM103: Needless bool (1 occurrence)
- B033: Duplicate value in stopwords (1 occurrence)

**Fix**:
1. Run `ruff check src/ --fix` to auto-fix most issues
2. Manually verify the fixes
3. For B033, remove duplicate `"dieser"` from `src/pdf_renamer/tokenization/stopwords.py`

**Code Changes**:
- Automatic import sorting will be handled by ruff
- Remove unused `import re` from `src/pdf_renamer/naming/title.py`
- Simplify `title.py:45-48` to `return not title.isupper()`
- Remove duplicate `"dieser"` from stopwords list

**Test Updates**:
- Run linting again to confirm all issues resolved
- Ensure no functional changes affect tests

**Validation**:
- Run `ruff check src/` should report 0 errors
- Run `ruff format src/` to ensure consistent formatting

### Phase 4: Fix Mypy Errors (Medium)

**Location**: Multiple files

**Issues**:
- Missing library stubs for nltk and langdetect (not fixable by us, can ignore)
- `LangdetectDetector.detect()` returns `Any` (line 49)
- Potential other type mismatches

**Fix**:
1. Add `# type: ignore[import-untyped]` for nltk and langdetect imports
2. Add explicit return type cast for `langdetect.detect()`
3. Run mypy to identify any remaining type errors

**Code Changes**:
```python
# In language/detector.py
from langdetect import detect  # type: ignore[import-untyped]

def detect(self, text: str) -> str:
    try:
        result: str = detect(text)
        return result
    except Exception as e:
        logger.warning("Language detection failed: %s, defaulting to 'en'", e)
        return "en"
```

**Test Updates**:
- Run mypy on entire src/ to verify no new errors
- Ensure existing tests still pass

**Validation**:
- Run `mypy src/ --ignore-missing-imports`
- No new type errors introduced

### Phase 5: Eliminate Duplicate PDF Reads (Medium)

**Location**: `src/pdf_renamer/processing/pipeline.py` (lines 82 and 92)

**Issue**: The PDF is opened twice: once in `self._extractor.extract()` and again in `self._extract_title_candidate()`. This doubles I/O operations.

**Fix**:
1. Modify `PdfTextExtractor.extract()` to return both text and metadata (title candidate)
2. Or create a `PdfDocument` dataclass that caches the PDF content
3. Update pipeline to use cached data

**Simpler Approach**: Since `PdfTextExtractor` already extracts text, we can extract title candidate from the same text content rather than re-reading the PDF. However, title extraction logic in `_extract_title_candidate` looks for specific patterns in the raw PDF text (including line breaks). The current text extraction already concatenates page text. We need to examine if title can be extracted from the already extracted text.

**Analysis**: The `_extract_title_candidate` method splits page text by newlines and looks for patterns. The `extract()` method concatenates page text with `text += reader.pages[i].extract_text() or ""`, losing page boundaries and newline structure. Therefore, we cannot simply reuse extracted text.

**Alternative Fix**: Cache the `PdfReader` object and pass it to both extraction methods. This requires modifying the `TextExtractor` interface or creating a new abstraction.

**Proposed Solution**:
1. Add a `PdfDocument` dataclass that loads PDF once and caches pages text with original formatting
2. Modify `PdfTextExtractor` to return `PdfDocument`
3. Update pipeline to use `PdfDocument` for both text and title extraction

**Implementation Steps**:
1. Create `src/pdf_renamer/models.py` (already exists) - add `PdfDocument` dataclass
2. Update `TextExtractor` interface to return `PdfDocument`
3. Update `PdfTextExtractor` to implement new interface
4. Update pipeline to use cached PDF data

**Code Changes**:
```python
# In models.py
@dataclass
class PdfDocument:
    path: Path
    num_pages: int
    pages: list[str]  # text per page with original formatting
    
    @classmethod
    def load(cls, path: Path, max_pages: int = 3) -> "PdfDocument":
        from pypdf import PdfReader
        reader = PdfReader(str(path))
        num_pages = min(len(reader.pages), max_pages)
        pages = []
        for i in range(num_pages):
            text = reader.pages[i].extract_text() or ""
            pages.append(text)
        return cls(path=path, num_pages=num_pages, pages=pages)

# In extraction/base.py
class TextExtractor(ABC):
    @abstractmethod
    def extract(self, path: Path, max_pages: int = 3) -> str:
        ...
    
    @abstractmethod
    def extract_document(self, path: Path, max_pages: int = 3) -> PdfDocument:
        ...

# In extraction/pdf.py
def extract_document(self, path: Path, max_pages: int = 3) -> PdfDocument:
    return PdfDocument.load(path, max_pages)

def extract(self, path: Path, max_pages: int = 3) -> str:
    doc = self.extract_document(path, max_pages)
    return "".join(doc.pages)
```

**Test Updates**:
- Update unit tests for `PdfTextExtractor` to test both methods
- Add integration test to verify PDF is only opened once
- Ensure existing functionality unchanged

**Validation**:
- Run performance benchmark with large PDFs to verify reduced I/O
- Ensure all existing tests pass

### Phase 6: Improve Language Detection Return Type (Low)

**Location**: `src/pdf_renamer/language/detector.py:47-49`

**Issue**: `langdetect.detect()` returns `Any`, but we declared return type as `str`.

**Fix**: Already addressed in Phase 4 with type ignore and explicit cast.

**Additional Improvement**: Consider adding validation that returned language code is a valid ISO 639-1 code.

**Code Changes**:
```python
def detect(self, text: str) -> str:
    try:
        from langdetect import detect
        result = detect(text)
        # Validate result is a string
        if not isinstance(result, str):
            raise ValueError(f"Invalid language detection result: {result}")
        return result
    except Exception as e:
        logger.warning("Language detection failed: %s, defaulting to 'en'", e)
        return "en"
```

**Test Updates**:
- Add test case where `langdetect.detect()` returns non-string (mock)
- Add test case for valid language codes

**Validation**:
- Run `pytest tests/unit/test_detector.py -v`

### Phase 7: Enhance Error Handling (Low)

**Location**: Various extraction and processing modules

**Issues**:
- Some exceptions may be silently caught and only logged at debug level
- Missing validation for empty/invalid PDF files
- No timeout handling for long-running operations

**Fix**:
1. Review all try-except blocks and ensure appropriate log levels
2. Add validation for PDF files (size, corruption)
3. Consider adding timeout for PDF processing (using `signal` or `threading`)

**Code Changes**:
```python
# In extraction/pdf.py
def extract(self, path: Path, max_pages: int = 3) -> str:
    if not path.exists():
        logger.error("PDF file not found: %s", path)
        return ""
    if path.stat().st_size == 0:
        logger.warning("PDF file is empty: %s", path)
        return ""
    
    text = ""
    try:
        reader = PdfReader(str(path))
        # ... rest of extraction
    except PDFSyntaxError as e:
        logger.error("Corrupted PDF %s: %s", path, e)
    except Exception as e:
        logger.error("Unexpected error reading %s: %s", path, e)
    return text
```

**Test Updates**:
- Add tests for missing files
- Add tests for empty PDF files
- Add tests for corrupted PDF files (mock exceptions)

**Validation**:
- Run tests with various edge cases
- Verify error messages are informative

### Phase 8: Minor Improvements (Low)

**Location**: Various files

**Improvements**:
1. **Documentation**: Add missing docstrings to private methods
2. **Code Style**: Ensure consistent naming and formatting
3. **Test Coverage**: Add integration tests for batch processing

**Code Changes**:
- Add docstrings to `_extract_title_candidate` and `_try_naming_strategies`
- Ensure all public functions have complete docstrings
- Add integration test for `RenamerOrchestrator` with multiple PDFs

**Test Updates**:
- Create integration test directory with sample PDFs
- Add test for batch processing with mixed success/skip cases

**Validation**:
- Run `pytest --cov=src` to check coverage
- Review documentation for completeness

## Testing Strategy

### Unit Tests
- Run existing unit tests after each phase
- Add new tests for each fix
- Use mocking for external dependencies (PyPDF2/pypdf, NLTK, langdetect)

### Integration Tests
- Create integration tests for end-to-end workflow
- Use real PDF files from test fixtures
- Test with different languages (English, German, Turkish)

### Regression Testing
- After each fix, run full test suite
- Compare output with baseline using sample directory
- Verify no changes in renaming behavior for existing PDFs

### Performance Testing
- Benchmark PDF processing before/after duplicate read fix
- Measure memory usage for large PDFs

## Validation Checklist

- [ ] All critical bugs fixed (type mismatch, deprecation)
- [ ] Linting passes with zero errors
- [ ] Mypy passes with acceptable ignores
- [ ] All existing tests pass
- [ ] New tests added for each fix
- [ ] No regression in renaming behavior
- [ ] Performance improved (if applicable)
- [ ] Documentation updated
- [ ] Commit messages follow conventional format

## Risk Considerations

### Migration Risks
- **pypdf vs PyPDF2 API differences**: Test thoroughly with various PDF formats
- **NLTK version compatibility**: Ensure stopwords and tokenizers work with current NLTK

### Performance Risks
- **Memory usage**: Caching PDF documents may increase memory footprint
- **Concurrency**: Current implementation is single-threaded; no concurrency issues

### Compatibility Risks
- **Python version**: Must maintain Python >=3.12 compatibility
- **Platform**: Ensure path handling works on Windows, Linux, macOS

## Timeline Estimate

| Phase | Estimated Time | Dependencies |
|-------|----------------|--------------|
| 1 | 1 hour | None |
| 2 | 2 hours | Phase 1 |
| 3 | 30 minutes | None |
| 4 | 1 hour | None |
| 5 | 3 hours | Phase 2 |
| 6 | 1 hour | Phase 4 |
| 7 | 2 hours | Phase 2 |
| 8 | 2 hours | All previous |

**Total Estimated Time**: ~12 hours over 2-3 days

## Next Steps

1. Review and approve this plan
2. Create a Git branch for fixes: `fix/issues-2026-04-01`
3. Implement phases sequentially
4. Run full test suite after each phase
5. Create pull request for review
6. Merge after approval

---

*Plan created: 2026-04-01*
