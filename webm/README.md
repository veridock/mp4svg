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
python video2svg.py output.webm output.svg
```
```bash
python webm/mp2webm.py 1.mp4 1.webm --copy
python video2svg.py 1.webm 1.svg
```
```bash
python video2svg.py 1.mp4 1.svg
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
