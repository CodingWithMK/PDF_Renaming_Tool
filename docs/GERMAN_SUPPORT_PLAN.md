# German Language Support - Implementation Plan

## Executive Summary

This document outlines the implementation of German language support for the PDF Renaming Tool. German is added as a third language alongside English and Turkish, following the SOLID-compliant architecture from Phase 2.

---

## 1. Why German?

| Factor | Rationale |
|--------|-----------|
| Market demand | German is the most spoken native language in Europe |
| Technical complexity | German has unique challenges (compound words, umlauts) that validate the architecture |
| Stopword density | German has high-frequency stopwords that significantly impact keyword extraction quality |

---

## 2. German-Specific Challenges

### 2.1 Compound Words (Komposita)

German frequently combines words:
- `Donaudampfschifffahrt` (Danube steamship navigation)
- `Krankenversicherungskarte` (health insurance card)

**Strategy:** NLTK tokenizer handles most compounds. For PDF titles, compound words are often kept intact, which is beneficial for filename uniqueness.

### 2.2 Umlauts and Special Characters

German uses: `ä`, `ö`, `ü`, `ß` (and uppercase `Ä`, `Ö`, `Ü`)

**Strategy:** Preserve umlauts in filenames (modern filesystems support them). Provide optional transliteration:
- `ä` -> `ae`
- `ö` -> `oe`
- `ü` -> `ue`
- `ß` -> `ss`

### 2.3 Case Sensitivity

German nouns are always capitalized (unlike English/Turkish). This actually helps title detection since titles are noun-heavy.

---

## 3. Custom German Stopwords

### Core stopwords (high-frequency, low-information):
```
der, die, das, den, dem, des, ein, eine, einem, einen, einer
und, oder, aber, sondern, doch, sondern
ist, sind, war, waren, wird, werden, wurde, wurden
auf, an, in, mit, von, zu, für, bei, nach, aus
sich, ich, du, er, sie, wir, ihr, man
dass, ob, wenn, weil, als, wie, was, wer, wo
auch, noch, schon, nur, sehr, so, da, hier, dort
dann, nun, ja, nein, mal, doch
nicht, kein, keine, keinen, keinem, keiner
über, unter, zwischen, neben, vor, hinter
alle, jede, jeder, jedes, alles
diese, dieser, dies, diesen, diesem, dieser
mehr, moins, andere, anderen, anderer, anderes
kann, können, muss, müssen, soll, sollen, will, wollen, darf, dürfen, mag, mögen
machen, machen, gehen, gehen, kommen, kommen, sehen, sehen
zwei, drei, vier, fünf, sechs, sieben, acht, neun, zehn
jahr, jahre, jahren, zeit, mal, fois
hier, dort, überall, nirgends
immer, oft, manchmal, selten, nie
bis, seit, während, ohne, gegen, um
```

### Document-specific stopwords (low-value for filenames):
```
kapitel, seite, seiten, bild, tabelle, abbildung, beispiel
siehe, vgl, usw, etc, ca, bzw
durch, damit, dazu, dafür, dazu, hierbei
autoren, autor, verfasser, herausgeber
```

---

## 4. Architecture Integration

### 4.1 New File: `tokenization/german.py`

```python
class GermanTokenizer(Tokenizer):
    """German tokenizer using NLTK with compound-aware filtering."""
    
    def __init__(self, custom_stopwords: set[str] | None = None):
        self._stopwords = GERMAN_STOPWORDS | (custom_stopwords or set())
    
    def tokenize(self, text: str) -> list[str]:
        # 1. Lowercase
        # 2. Remove punctuation
        # 3. NLTK word_tokenize
        # 4. Filter: alphabetic, not in stopwords, length > 3
        ...
```

### 4.2 Registration in Container

```python
def _build_tokenizer_registry(self) -> TokenizerRegistry:
    reg = TokenizerRegistry()
    reg.register("en", EnglishTokenizer())
    reg.register("tr", TurkishTokenizer())
    reg.register("de", GermanTokenizer())  # NEW
    return reg
```

### 4.3 Slugifier Enhancement

```python
# In naming/slugifier.py
GERMAN_TRANSLITERATION = {
    "ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss",
    "Ä": "Ae", "Ö": "Oe", "Ü": "Ue",
}
```

---

## 5. Step-by-Step Implementation

| Step | File | Action |
|------|------|--------|
| 1 | `src/pdf_renamer/tokenization/__init__.py` | Create package |
| 2 | `src/pdf_renamer/tokenization/base.py` | Create `Tokenizer` ABC |
| 3 | `src/pdf_renamer/tokenization/stopwords.py` | Add `GERMAN_STOPWORDS` constant |
| 4 | `src/pdf_renamer/tokenization/english.py` | Extract `EnglishTokenizer` |
| 5 | `src/pdf_renamer/tokenization/turkish.py` | Extract `TurkishTokenizer` |
| 6 | `src/pdf_renamer/tokenization/german.py` | Create `GermanTokenizer` |
| 7 | `src/pdf_renamer/tokenization/registry.py` | Create `TokenizerRegistry` |
| 8 | `tests/unit/test_tokenizers.py` | Test all tokenizers |

---

## 6. Test Strategy

### Unit Tests for GermanTokenizer

```python
class TestGermanTokenizer:
    def test_tokenize_basic(self):
        tokenizer = GermanTokenizer()
        result = tokenizer.tokenize("Das ist ein Test")
        assert "das" not in result  # stopword filtered
        assert "test" in result
    
    def test_tokenize_filters_stopwords(self):
        tokenizer = GermanTokenizer()
        result = tokenizer.tokenize("Der schnelle braune Fuchs")
        assert "der" not in result
    
    def test_tokenize_preserves_umlauts(self):
        tokenizer = GermanTokenizer()
        result = tokenizer.tokenize("Ärzte überprüfen Öffnungszeiten")
        assert "ärzte" in result
        assert "überprüfen" in result
    
    def test_tokenize_compound_words(self):
        tokenizer = GermanTokenizer()
        result = tokenizer.tokenize("Krankenversicherungskarte")
        # Compound should be preserved as single token
        assert "krankenversicherungskarte" in result
```

---

## 7. Performance Expectations

| Metric | Before (EN/TR only) | After (EN/TR/DE) |
|--------|---------------------|------------------|
| Tokenizer lookup time | O(1) | O(1) (registry) |
| German stopwords count | N/A | ~150 words |
| Additional memory | 0 | ~2KB for German stopwords |
| Import time increase | N/A | Negligible (lazy load) |

---

## 8. Validation Checklist

- [ ] German PDFs are detected correctly by `langdetect`
- [ ] German stopwords are filtered from tokenized text
- [ ] German umlauts are preserved in filenames (default)
- [ ] German umlauts can be transliterated (optional mode)
- [ ] Compound words are handled as single tokens
- [ ] All tokenizers have unit tests with >90% coverage
- [ ] Registry lookup for "de" returns `GermanTokenizer`
