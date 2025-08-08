Widzę, że głównym problemem jest konwersja klatek do AVIF, która jest **ekstremalnie wolna**. Oto kilka rozwiązań dla maksymalnej szybkości:

## 1. **NAJSZYBSZE - Pomiń ekstrakcję klatek i użyj tradycyjnej konwersji**
```bash
python mp4webm.py input.mp4 output.webm --no-frames
```

## 2. **Ulepszona wersja skryptu - tylko szybka konwersja**## Użycie nowego skryptu:

### **Najszybsze opcje:**

1. **Direct Copy** (natychmiastowe, jeśli kodek jest kompatybilny):
```bash
python webm/mp2webm.py input.mp4 output.webm --copy
python webm/video2svg.py output.webm output.svg
```
```bash
python webm/mp2webm.py 1.mp4 1.webm --copy
python webm/video2svg.py 1.webm 1.svg
```
```bash
python webm/video2svg.py 1.mp4 1.svg
```

2. **Ultra-fast** (5-10 sekund dla typowych wideo):
```bash
python webm/mp2webm.py input.mp4 output.webm --ultrafast
```

3. **Hardware acceleration** (3-8 sekund z GPU):
```bash
python webm/mp2webm.py input.mp4 output.webm --hardware
```

### **Dla oryginalnego skryptu - najszybsze użycie:**
```bash
# Pomiń ekstrakcję klatek i użyj tradycyjnej konwersji
python mp4webm.py input.mp4 output.webm --no-frames

# Lub jeśli chcesz smart conversion bez klatek
python mp4webm.py input.mp4 output.webm --smart-conversion --ultra-fast --no-frames
```

## **Główne problemy w oryginalnym skrypcie:**

1. **Konwersja do AVIF** - używa `libaom-av1` który jest EKSTREMALNIE wolny (może zajmować 5-10 sekund na klatkę!)
2. **Ekstrakcja 100 klatek** - niepotrzebna dla samej konwersji
3. **Analiza każdej klatki** - dodaje overhead

## **Porównanie szybkości:**

| Metoda | Czas | Jakość |
|--------|------|--------|
| Direct copy | <1s | Oryginalna |
| Ultra-fast (nowy skrypt) | 5-10s | Dobra |
| Hardware GPU | 3-8s | Dobra |
| Oryginalny --no-frames | 10-20s | Bardzo dobra |
| Oryginalny z klatkami | 2-10 min | Bardzo dobra |



Poprawię skrypt `video2svg.py` aby obsługiwał audio i dodał kontrolki odtwarzania:## Poprawiony skrypt z obsługą audio

Główne ulepszenia w nowym skrypcie:

### **1. Obsługa Audio** 🔊
- **Domyślnie włączone kontrolki** - użytkownik może sterować dźwiękiem
- **Automatyczne wykrywanie audio** - sprawdza czy video ma ścieżkę dźwiękową
- **Wskaźnik audio** - pokazuje "🔊 With Audio" na miniaturze
- **Inteligentne odmutowanie** - JavaScript automatycznie włącza dźwięk przy kliknięciu

### **2. Nowe opcje komend:**

```bash
# Podstawowa konwersja z kontrolkami i audio
python webm/video2svg.py 1.mp4 1.svg

# Włącz audio od razu (bez wyciszenia)
python webm/video2svg.py 1.mp4 1.svg --unmuted --no-controls

# Autoplay z audio (większość przeglądarek wymusi wyciszenie)
python webm/video2svg.py 1.mp4 1.svg --autoplay --unmuted --no-controls

# Bez kontrolek, autoplay wyciszony
python webm/video2svg.py 1.webm loop.svg --autoplay --no-controls
```

### **3. Kluczowe zmiany:**

| Funkcja | Przed | Po |
|---------|-------|-----|
| **Audio** | Zawsze `muted="true"` | Domyślnie wyciszone, opcja `--unmuted` |
| **Kontrolki** | Brak | Domyślnie włączone `controls="true"` |
| **Autoplay z audio** | Niemożliwe | Próbuje, fallback na wyciszone |
| **Wykrywanie audio** | Brak | Automatyczne przez ffprobe |
| **Miniaturka** | PNG | JPEG (mniejszy rozmiar) |

### **4. Jak działa audio:**

1. **Przy otwarciu w przeglądarce:**
   - Jeśli użyto `--unmuted` - video startuje z dźwiękiem (po kliknięciu play)
   - Kontrolki pozwalają regulować głośność

2. **Zabezpieczenia przeglądarek:**
   - Większość przeglądarek blokuje autoplay z dźwiękiem
   - Skrypt automatycznie próbuje odmutować przy pierwszej interakcji użytkownika

3. **JavaScript inteligentnie obsługuje:**
   ```javascript
   // Próbuje odtworzyć z dźwiękiem
   video.muted = false;
   video.play().catch(() => {
       // Jeśli się nie uda, odtwarza wyciszone
       video.muted = true;
       video.play();
   });
   ```

### **5. Przykład użycia dla video z audio:**

```bash
# Konwertuj video z audio, pokaż kontrolki
python video2svg.py muzyka.mp4 muzyka.svg --unmuted

# Wynik:
# ✅ SVG z:
#    - Kontrolkami odtwarzania
#    - Przyciskiem głośności
#    - Audio włączone po kliknięciu play
#    - Wskaźnikiem "🔊 With Audio" na miniaturce
```

### **6. Wskazówki:**
- **Chrome/Firefox** - wymagają interakcji użytkownika dla audio
- **Safari** - może wymagać dodatkowego kliknięcia
- **Edge** - podobnie jak Chrome

