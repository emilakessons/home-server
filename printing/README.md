# Målarbildsutskrift

Söker upp målarbilder på nätet, konverterar till svartvit A4 och skriver ut via CUPS.

## Översikt

```
Home Assistant / Google Assistant
        │
        ▼
  rest_command (HA)  eller  curl → print API (:8787)
        │
        ▼
  coloring_printer (Docker)
        │
        ▼
  CUPS på värden (:631)  →  nätverksskrivare
```

| Komponent | Var | Port |
|-----------|-----|------|
| **CUPS** (skrivarserver) | Värden (Raspberry Pi) | **631** |
| **Print API** | `coloring_printer`-container | **8787** |
| **Home Assistant** | `homeassistant`-container | 8123 |

Skrivarnamnet i koden är **`Skrivare`**. Om du byter namn i CUPS måste du uppdatera `print_coloring_page.py`.

---

## CUPS – webbgränssnitt

CUPS körs på **värden**, inte i containern. Öppna i webbläsaren:

```
http://localhost:631
http://<pi-ip>:631          # t.ex. http://192.168.1.242:631
```

Där kan du:

- **Administration → Hantera skrivare** – se status, kö, pausa
- **Administration → Lägg till skrivare** – lägga till ny skrivare
- **Administration → Hantera jobb** – avbryta fastnade utskrifter

På Raspberry Pi OS kan du också öppna **Inställningar → Skrivare** – det använder samma CUPS under huven.

### Första gången / autentisering

CUPS kan kräva inloggning med en användare i gruppen `lpadmin`:

```bash
sudo usermod -aG lpadmin $USER
```

Logga ut och in igen efteråt. Vid behov:

```bash
sudo systemctl restart cups
```

---

## CUPS – kommandorad

Alla kommandon körs på **värden** (Pi:n), inte i containern.

```bash
# Lista skrivare och status
lpstat -a
lpstat -p
lpstat -v

# Skriv ut en fil
lp -d "Skrivare" /sökväg/till/fil.png

# Se utskriftskö
lpq -P Skrivare

# Avbryt alla jobb på en skrivare
cancel -a Skrivare

# Sätt standardskrivare
lpoptions -d Skrivare
```

### Lägga till nätverksskrivare (IPP)

Om skrivaren har IP-adress (t.ex. Brother på `192.168.1.222`):

```bash
# Hitta skrivare på nätet (valfritt)
lpinfo -v

# Lägg till via IPP
sudo lpadmin -p Skrivare -E \
  -v "ipp://192.168.1.222/ipp" \
  -m everywhere \
  -L "Skrivare"

# Aktivera och sätt som standard
sudo cupsenable Skrivare
sudo cupsaccept Skrivare
sudo lpoptions -d Skrivare
```

Byt `-p Skrivare` och `-v ipp://...` till dina värden. Kontrollera med `lpstat -v`.

### Ta bort skrivare

```bash
sudo lpadmin -x Skrivare
```

---

## Print API (port 8787)

Containern `coloring_printer` exponerar ett enkelt HTTP-API på **port 8787** (`network_mode: host`).

| Endpoint | Metod | Beskrivning |
|----------|-------|-------------|
| `/health` | GET | Hälsokoll |
| `/print` | POST | Starta utskrift |

Exempel:

```bash
curl http://127.0.0.1:8787/health

curl -X POST http://127.0.0.1:8787/print \
  -H "Content-Type: application/json" \
  -d '{"subject": "paw patrol chase"}'
```

Svar `202` betyder att jobbet startats i bakgrunden (sök + nedladdning + utskrift tar tid).

### Shell-wrapper

```bash
./print_coloring_page.sh "Bamse"
```

### Docker

```bash
cd /opt/home-server

# Bygg och starta
docker compose up -d --build coloring_printer

# Loggar
docker logs -f coloring_printer

# Testa inuti containern
docker exec coloring_printer lpstat -a
```

Containern monterar värdens CUPS:

- `/var/run/cups` – socket till CUPS
- `/etc/cups` – skrivarkonfiguration (read-only)

Därför måste CUPS köra på **värden**:

```bash
sudo systemctl status cups
sudo systemctl enable --now cups
```

---

## Filer och mappar

| Sökväg | Innehåll |
|--------|----------|
| `print_coloring_page.py` | Sök, bearbeta och skriv ut |
| `print_api.py` | HTTP-API för Home Assistant |
| `print_coloring_page.sh` | Manuellt test via curl |
| `downloads/` | Nedladdade originalbilder (gitignored) |
| `output/` | Färdiga PNG:er före utskrift (gitignored) |

På värden ligger CUPS-konfiguration i `/etc/cups/` (viktigast: `printers.conf`).

---

## Home Assistant

HA anropar print API via `rest_commands.yaml`:

```yaml
rest_command.print_coloring_page:
  url: http://127.0.0.1:8787/print
  ...
```

Google Assistant använder script i `homeassistant/scripts.yaml` (t.ex. *"aktivera skriv ut en bild på Bamse"*), som i sin tur anropar samma API.

---

## Felsökning

### Skrivaren syns inte

```bash
lpstat -a
lpstat -v
ping 192.168.1.222    # skrivarens IP
```

Kontrollera att skrivaren är påslagen och att IP stämmer i `lpstat -v`.

### Utskrift från container men inte från Pi (eller tvärtom)

```bash
# På värden
lp -d "Skrivare" /opt/home-server/printing/output/test.png

# Från container
docker exec coloring_printer lp -d "Skrivare" /app/output/test.png
```

Om värden funkar men inte containern: kontrollera att `/var/run/cups` och `/etc/cups` är monterade i `docker-compose.yml`.

### CUPS-webben når inte (:631)

```bash
sudo systemctl status cups
ss -tlnp | grep 631
```

Brandvägg: tillåt port **631/tcp** om du öppnar från annan dator i nätet.

### Print API svarar inte (:8787)

```bash
docker ps --filter name=coloring_printer
docker logs coloring_printer --tail 50
curl http://127.0.0.1:8787/health
```

Starta om:

```bash
docker compose restart coloring_printer
```

### Fel skrivarnamn

Koden använder hårdkodat namn `Skrivare`:

```python
os.system(f'lp -d "Skrivare" "{output_file}"')
```

Byt till ditt CUPS-namn om det skiljer sig, eller döp om skrivaren:

```bash
sudo lpadmin -p GammaltNamn -o printer-is-shared=false
# eller lägg till ny med rätt namn och ta bort gammal
```

### Jobb fastnar i kön

```bash
lpq -P Skrivare
cancel -a Skrivare
sudo systemctl restart cups
```

---

## Snabbreferens

| Vad | Var / hur |
|-----|-----------|
| CUPS webb-UI | `http://<pi-ip>:631` |
| Print API | `http://<pi-ip>:8787/health` |
| Skrivarnamn | `Skrivare` |
| Manuell utskrift | `./print_coloring_page.sh "motiv"` |
| CUPS-tjänst | `sudo systemctl restart cups` |
| Container | `docker compose restart coloring_printer` |
