# Studio Accettura — Guida completa all'installazione
## Da zero all'app sul telefono in 20 minuti

---

## COSA TI SERVE
- Un computer (anche il più vecchio) per la configurazione iniziale
- Connessione internet
- Carta di credito (solo per Anthropic API, ~$5/mese per uso normale)
- Smartphone (iOS o Android)

---

## PASSO 1 — Installa Python sul computer
1. Vai su **python.org/downloads**
2. Scarica Python 3.11 o superiore
3. Installa — su Windows spunta "Add Python to PATH"
4. Verifica: apri il Terminale (Mac) o Prompt dei comandi (Windows) e scrivi:
   ```
   python --version
   ```
   Deve apparire qualcosa tipo `Python 3.11.x`

---

## PASSO 2 — Scarica i file del progetto
1. Scarica tutti i file che ti ho fornito
2. Crea una cartella sul desktop chiamata `accettura`
3. Metti dentro questa struttura:
   ```
   accettura/
   ├── app.py
   ├── database.py
   ├── claude_client.py
   ├── pdf_hep.py
   ├── styles.py
   ├── requirements.txt
   ├── .streamlit/
   │   └── config.toml
   └── pages/
       ├── 1_Nuovo_Paziente.py
       ├── 2_Archivio.py
       ├── 3_Agenda.py
       └── 4_Impostazioni.py
   ```

---

## PASSO 3 — Installa le librerie
Apri il Terminale/Prompt dei comandi, entra nella cartella e installa:
```bash
cd Desktop/accettura
pip install -r requirements.txt
```
Attendi il download (2-3 minuti).

---

## PASSO 4 — Ottieni la chiave API di Anthropic
1. Vai su **console.anthropic.com**
2. Crea un account gratuito
3. Vai su "API Keys" → "Create Key"
4. Copia la chiave (inizia con `sk-ant-...`)
5. Ricarica la carta con $5-10 (durano mesi con uso normale)

---

## PASSO 5 — Configura la chiave API

**Mac/Linux:**
```bash
export ANTHROPIC_API_KEY="sk-ant-la-tua-chiave"
```

**Windows (PowerShell):**
```powershell
$env:ANTHROPIC_API_KEY="sk-ant-la-tua-chiave"
```

Per renderla permanente su Mac, aggiungi quella riga al file `~/.zshrc`.
Su Windows, impostala nelle variabili d'ambiente di sistema.

---

## PASSO 6 — Avvia l'app in locale
```bash
cd Desktop/accettura
streamlit run app.py
```
Si aprirà automaticamente nel browser: **http://localhost:8501**

---

## PASSO 7 — Pubblica online (per usarla dal telefono) — GRATUITO

### 7a. Crea un account GitHub (gratis)
1. Vai su **github.com** → Sign up
2. Crea un nuovo repository: clicca "+" → "New repository"
3. Nome: `studio-accettura` → crea

### 7b. Carica i file
1. Nel repository, clicca "uploading an existing file"
2. Trascina TUTTA la cartella `accettura`
   (attenzione: la cartella `.streamlit` potrebbe essere nascosta su Mac — premi Cmd+Shift+.)
3. Scrivi "Prima versione" nel messaggio → Commit

### 7c. Deploy su Streamlit Cloud (gratis)
1. Vai su **share.streamlit.io** → Sign in with GitHub
2. Clicca **"New app"**
3. Seleziona il repository `studio-accettura`
4. Main file path: `app.py`
5. Clicca **"Advanced settings"** → sezione **Secrets**
6. Incolla esattamente:
   ```
   ANTHROPIC_API_KEY = "sk-ant-la-tua-chiave"
   ```
7. Clicca **Deploy**

In 2-3 minuti hai un link tipo:
**https://studio-accettura.streamlit.app**

---

## PASSO 8 — Installa come app sul telefono (MINI-APP GRATUITA)

### iPhone (Safari):
1. Apri il link dell'app in **Safari** (non Chrome)
2. Tocca l'icona **Condividi** (il quadrato con la freccia in su)
3. Scorri e tocca **"Aggiungi alla schermata Home"**
4. Dai un nome tipo "Studio Accettura"
5. Tocca **Aggiungi**
6. L'icona appare nella schermata home come un'app normale

### Android (Chrome):
1. Apri il link in **Chrome**
2. Tocca i tre puntini in alto a destra
3. Tocca **"Aggiungi alla schermata Home"** o **"Installa app"**
4. Conferma

**Risultato:** si apre a schermo intero senza barra del browser, come un'app nativa. Gratis.

---

## AGGIORNAMENTI FUTURI
Quando vuoi modificare qualcosa (prompt, layout, funzioni):
1. Modifica il file sul computer
2. Vai su GitHub → apri il file → icona matita → incolla il nuovo contenuto → Commit
3. Streamlit si aggiorna automaticamente in ~1 minuto

---

## COSTI STIMATI
| Servizio | Costo |
|---|---|
| Streamlit Cloud | **GRATIS** |
| GitHub | **GRATIS** |
| Python | **GRATIS** |
| Anthropic API | ~$0.002 per seduta (praticamente gratis) |
| **TOTALE** | **~$1-3/mese** |

---

## PROBLEMI COMUNI

**"Module not found"** → ricollegati e riesegui `pip install -r requirements.txt`

**"Invalid API Key"** → controlla che la chiave in Secrets sia esatta, senza spazi

**L'app non si aggiorna** → su Streamlit Cloud, clicca i tre puntini → "Reboot app"

**Il file .streamlit non si vede** → su Mac premi Cmd+Shift+. per vedere i file nascosti
