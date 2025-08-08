# WebM Tools - Fast Video Conversion & SVG Generation

Szybkie narzędzia do konwersji video i generowania SVG z obsługą audio.

## 🚀 Najszybsze rozwiązania

### **Problem z głównym skryptem mp4webm.py:**
Konwersja do AVIF jest **ekstremalnie wolna** (5-10 sekund na klatkę!) - to główny bottleneck.

### **1. Szybka konwersja bez klatek**
```bash
# Pomiń ekstrakcję klatek - znacznie szybciej
python mp4webm.py input.mp4 output.webm --no-frames

# Ultra-fast smart conversion
python mp4webm.py input.mp4 output.webm --smart-conversion --ultra-fast --no-frames
```

### **2. Nowe narzędzia webm/ (najszybsze)**

#### **A) mp2webm.py - Super-szybka konwersja**
```bash
# Direct copy (natychmiastowe)
python webm/mp2webm.py 1.mp4 1.webm --copy

# Ultra-fast (5-10 sekund)
python webm/mp2webm.py input.mp4 output.webm --ultrafast

# Hardware acceleration (3-8 sekund)
python webm/mp2webm.py input.mp4 output.webm --hardware
```

#### **B) video2svg.py - Video→SVG z audio**
```bash
# Podstawowe użycie
python webm/video2svg.py 1.mp4 1.svg
python webm/video2svg.py 1.webm 1.svg

# Bezpośrednie MP4→SVG (pomiń WebM)
python webm/video2svg.py input.mp4 output.svg
```

## 📊 Porównanie szybkości

| Metoda | Czas | Jakość | Przypadek użycia |
|--------|------|--------|------------------|
| **Direct copy** | <1s | Oryginalna | Kompatybilne kodeki |
| **Ultra-fast** | 5-10s | Dobra | Szybka konwersja |
| **Hardware GPU** | 3-8s | Dobra | Z akceleracją |
| **mp4webm.py --no-frames** | 10-20s | Bardzo dobra | Bez ekstraktów |
| **mp4webm.py (pełne)** | 2-10 min | Bardzo dobra | Analiza + klatki |

## 🔊 video2svg.py - Obsługa Audio

### **Główne funkcje:**
- ✅ **Automatyczne wykrywanie audio** (ffprobe)
- ✅ **Kontrolki odtwarzania** (domyślnie włączone)
- ✅ **Ikona play** (zawsze widoczna w preview)
- ✅ **Wskaźnik audio** ("🔊 Audio" na miniaturce)
- ✅ **Autoplay zgodny z przeglądarkami**

### **Przykłady użycia:**
```bash
# Podstawowe - z kontrolkami i audio
python webm/video2svg.py 1.mp4 output.svg

# Autoplay z audio (wymaga kliknięcia dla dźwięku)
python webm/video2svg.py 1.mp4 output.svg --autoplay --unmuted

# Bez kontrolek, tylko autoplay
python webm/video2svg.py 1.mp4 output.svg --autoplay --no-controls

# Duża ikona play dla lepszej widoczności
python webm/video2svg.py 1.mp4 output.svg --play-button-size 60
```

### **Kluczowe opcje:**

| Opcja | Opis | Uwagi |
|-------|------|-------|
| `--autoplay` | Automatyczne odtwarzanie | Zawsze wyciszone (wymóg przeglądarek) |
| `--unmuted` | Włącz audio po interakcji | Dla autoplay: klik = dźwięk |
| `--no-controls` | Ukryj kontrolki | Minimalistyczny wygląd |
| `--play-button-size N` | Rozmiar ikony play | Domyślnie 40px |

## 🎯 Zalecane workflow

### **Dla maksymalnej szybkości:**
```bash
# 1. Direct conversion (jeśli możliwe)
python webm/mp2webm.py 1.mp4 1.webm --copy
python webm/video2svg.py 1.webm output.svg

# 2. Lub bezpośrednio MP4→SVG
python webm/video2svg.py 1.mp4 output.svg
```

### **Dla najlepszej jakości:**
```bash
# Smart conversion z analizą klatek
python mp4webm.py 1.mp4 optimized.webm --smart-conversion --ultra-fast
python webm/video2svg.py optimized.webm final.svg --unmuted
```

## 🌐 Kompatybilność przeglądarek

### **Audio autoplay:**
- **Chrome/Edge:** Wymaga kliknięcia dla dźwięku
- **Firefox:** Podobnie jak Chrome  
- **Safari:** Może wymagać dodatkowej interakcji

### **Polityka bezpieczeństwa:**
```javascript
// ❌ BLOKOWANE przez przeglądarki
<video autoplay unmuted>

// ✅ DOZWOLONE
<video autoplay muted> + JavaScript unmute po kliknięciu
```

## 🔧 Rozwiązywanie problemów

**Q: Autoplay nie działa z dźwiękiem**  
A: To normalne - użyj `--autoplay --unmuted` (klik włączy audio)

**Q: Konwersja jest wolna**  
A: Użyj `--no-frames` lub narzędzi z `webm/`

**Q: Brak ikony play w preview**  
A: Ikona jest zawsze widoczna - sprawdź `--play-button-size`

---
