# ArchiMEDe — App Blueprint

**Versione:** 1.0
**Data:** Marzo 2026
**Stato:** Documento di design — non implementato

> **ArchiMEDe** è un assistente statistico personale per medici clinici.
> Il medico carica i suoi dati, dialoga con l'agente in linguaggio naturale,
> ottiene analisi statistiche appropriate e scarica un report completo.
> Plug-and-play. Nessuna competenza statistica richiesta.

---

## Indice

1. [Visione del prodotto](#1-visione-del-prodotto)
2. [Architettura generale](#2-architettura-generale)
3. [Componente locale — Desktop App](#3-componente-locale--desktop-app)
4. [Componente server](#4-componente-server)
5. [Anonimizzazione](#5-anonimizzazione)
6. [Flusso utente end-to-end](#6-flusso-utente-end-to-end)
7. [Session store](#7-session-store)
8. [Report PDF](#8-report-pdf)
9. [Billing e tiers](#9-billing-e-tiers)
10. [Privacy, GDPR e T&C](#10-privacy-gdpr-e-tc)
11. [Stack tecnico](#11-stack-tecnico)
12. [Roadmap](#12-roadmap)

---

## 1. Visione del prodotto

### Il problema

I medici clinici raccolgono dati di qualità ma non hanno le competenze statistiche
per analizzarli. Le alternative attuali (biostatistico, SPSS, consulente esterno)
sono costose, lente, o richiedono formazione.

### La soluzione

Un'app desktop che il medico scarica sul proprio PC. L'app:
1. Legge i dati localmente e li anonimizza prima che escano dalla macchina
2. Connette il medico a un agente AI (ArchiMEDe) che lo guida attraverso l'analisi
3. Genera un report PDF scaricabile con spiegazioni, analisi e spazio per l'interpretazione clinica

### Principi guida

- **Privacy-by-design:** nessun dato identificativo lascia il PC del medico
- **Plug-and-play:** nessuna installazione di dipendenze, nessuna configurazione
- **Medico al centro:** l'agente spiega, propone, chiede conferma — non decide
- **Pay-per-report:** si paga solo quando si ottiene un risultato concreto

---

## 2. Architettura generale

```
┌──────────────────────────────────────────────────────────────┐
│                      PC del medico                           │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐  │
│  │              App desktop (Tauri)                       │  │
│  │                                                        │  │
│  │  ┌──────────────────┐    ┌────────────────────────┐   │  │
│  │  │  Presidio locale │    │   UI (chat + upload)   │   │  │
│  │  │  - PII dataset   │    │   - drag & drop file   │   │  │
│  │  │  - PII messaggi  │    │   - chat con agente    │   │  │
│  │  │  - mapping locale│    │   - download report    │   │  │
│  │  └────────┬─────────┘    └───────────┬────────────┘   │  │
│  │           │ dati anonimi              │ messaggi anonimi│  │
│  └───────────┼───────────────────────────┼────────────────┘  │
└──────────────┼───────────────────────────┼────────────────────┘
               │           HTTPS           │
               └─────────────┬─────────────┘
                             │
┌────────────────────────────▼─────────────────────────────────┐
│                    Server (EU)                                │
│                                                              │
│  ┌─────────────┐   ┌──────────────┐   ┌──────────────────┐  │
│  │  FastAPI    │   │  Redis       │   │  Claude API      │  │
│  │  backend   ◄───►  session     │   │  (Agente con     │  │
│  │            │   │  store       │   │   skills)        │  │
│  └─────────────┘   └──────────────┘   └──────────────────┘  │
│                                                              │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │  Report generator (PDF)                                 │ │
│  └─────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────┘
```

---

## 3. Componente locale — Desktop App

### Tecnologia

**Tauri** (Rust + WebView) — framework per app desktop cross-platform.
- Bundle finale: ~5-10 MB (vs ~150 MB di Electron)
- Cross-platform: Windows, macOS, Linux
- La UI è web (HTML/CSS/JS o React), il backend locale è Rust
- Nessuna dipendenza da installare per il medico: scarica un `.exe` / `.dmg` / `.AppImage`

### Responsabilità del componente locale

1. **Upload e lettura del file** — Excel (.xlsx) e CSV letti localmente, mai inviati raw
2. **Anonimizzazione dataset** — Presidio scansiona tutte le colonne (vedi Sezione 5)
3. **Anonimizzazione messaggi** — ogni messaggio del medico passa per Presidio prima dell'invio
4. **Mapping locale** — dizionario `{valore_reale → placeholder}` salvato solo sul PC
5. **Gestione sessione** — mantiene il `session_id` per tutta la conversazione
6. **Download report** — riceve il PDF dal server e lo salva localmente
7. **Billing UI** — reindirizza a Stripe per il pagamento, riceve conferma

### Cosa NON fa il componente locale

- Non esegue analisi statistiche
- Non chiama direttamente il modello AI
- Non salva dati sul cloud

---

## 4. Componente server

### Tecnologia

**FastAPI** (Python) — leggero, asincrono, ottimo per API LLM-based.

### Responsabilità

1. **Autenticazione** — JWT token, rilasciato al login
2. **Gestione sessioni** — legge/scrive su Redis (vedi Sezione 7)
3. **Orchestrazione agente** — costruisce il prompt con skills e contesto, chiama Claude API
4. **Esecuzione analisi** — codice Python eseguito in sandbox isolato per sessione
5. **Generazione report PDF** — assembla il PDF a fine sessione
6. **Billing** — integrazione Stripe per verifica crediti e acquisto

### Hosting

- Provider europeo obbligatorio per GDPR (es. AWS `eu-west-1`, Hetzner DE, OVH FR)
- I dati di sessione su Redis hanno TTL di 4 ore — dopo vengono eliminati automaticamente
- Nessun dato paziente viene persistito dopo la sessione

---

## 5. Anonimizzazione

### Strumento: Microsoft Presidio

Libreria open source, gira interamente in locale sul PC del medico.
Riconosce e sostituisce automaticamente:

| Tipo PII | Esempi | Placeholder |
|---|---|---|
| Nomi propri | Gianbattista, Maria Rossi | `Paziente_A`, `Paziente_B` |
| Codici fiscali | RSSMRA80A01H501U | `[CF_RIMOSSO]` |
| Date di nascita | 03/05/1979 | `[DATA_RIMOSSA]` |
| Numeri di telefono | +39 333 1234567 | `[TEL_RIMOSSO]` |
| Indirizzi | Via Garibaldi 5, Roma | `[INDIRIZZO_RIMOSSO]` |
| Email | mario@ospedale.it | `[EMAIL_RIMOSSA]` |

### Flusso anonimizzazione dataset

```
File caricato dal medico
        │
        ▼
Presidio scansiona ogni cella
        │
        ▼
Mostra al medico: "Ho trovato questi valori potenzialmente identificativi:
[lista]. Li sostituisco con placeholder prima di procedere?"
        │
Medico conferma
        │
        ▼
Dataset anonimizzato → inviato al server
Mapping locale salvato sul PC (mai inviato)
```

### Flusso anonimizzazione messaggi

Ogni messaggio del medico — prima di essere inviato al server — passa per Presidio.
Se viene trovato PII:

```
Medico scrive: "Gianbattista ha 45 anni e lavora a Milano"
        │
Presidio rileva: "Gianbattista" (nome), "Milano" (città)
        │
        ▼
Messaggio trasformato: "Paziente_A ha 45 anni e lavora a Città_1"
        │
UI mostra al medico: "Ho rimosso: Gianbattista → Paziente_A, Milano → Città_1"
        │
        ▼
Messaggio anonimo inviato al server
```

### Limiti e responsabilità

Presidio esegue un best-effort. Descrizioni quasi-identificative ("il paziente
con gli occhi verdi che lavora in Via Garibaldi") non vengono rilevate
automaticamente. La responsabilità finale dell'anonimizzazione è del medico
(esplicitato nei T&C e nel disclaimer di sessione).

---

## 6. Flusso utente end-to-end

```
1. REGISTRAZIONE
   Medico scarica l'app → si registra con email → riceve 1 credito gratuito

2. UPLOAD
   Medico trascina il file Excel/CSV nell'app
   → Presidio scansiona e anonimizza
   → Medico vede riepilogo: "200 righe, 45 colonne, 3 valori anonimizzati"
   → Medico conferma

3. DIALOGO — FASE ELICITAZIONE
   Agente: "Benvenuto. Di che tipo di pazienti si tratta?"
   Medico: [risponde]
   Agente: [fa domande una alla volta fino a capire contesto clinico]
   Ogni messaggio del medico → filtrato da Presidio → inviato al server

4. DIALOGO — PROPOSTA ANALISI
   Agente propone piano di analisi con spiegazioni
   Medico approva o modifica
   Agente chiede conferma esplicita prima di procedere

5. ESECUZIONE ANALISI
   Analisi una alla volta, con spiegazione prima e dopo
   Grafici e tabelle mostrati in-app
   Medico può chiedere chiarimenti su ogni risultato

6. GENERAZIONE REPORT
   Medico clicca "Genera report"
   → Server assembla PDF (vedi Sezione 8)
   → App scarica il PDF localmente

7. PAGAMENTO
   Se il medico non ha crediti → reindirizzato a Stripe prima del download
   Se ha crediti → scalato automaticamente
```

---

## 7. Session store

**Tecnologia:** Redis con TTL = 4 ore dall'ultimo messaggio.

**Contenuto della sessione (chiave: `session:{session_id}`):**

```json
{
  "user_id": "...",
  "created_at": "...",
  "last_activity": "...",
  "dataset_summary": {
    "n_rows": 200,
    "n_cols": 45,
    "variable_types": {...},
    "missing_data": {...}
  },
  "clinical_context": {
    "population": "...",
    "outcome": "...",
    "predictors": [...],
    "subgroups": [...],
    "study_type": "..."
  },
  "conversation_history": [...],
  "analyses_completed": [...],
  "figures_generated": [...]
}
```

**Cosa NON è nella sessione:**
- Dati grezzi dei pazienti (mai inviati al server)
- Mapping di anonimizzazione (resta solo sul PC)
- Informazioni di billing

**Eliminazione:** alla scadenza del TTL Redis cancella automaticamente la sessione.
Nessun dato paziente viene persistito dopo 4 ore di inattività.

---

## 8. Report PDF

Il report è il prodotto finale che il medico scarica e può allegare alla tesi
o alla pubblicazione. Struttura:

```
1. COPERTINA
   ArchiMEDe | Data | [ID sessione anonimo per riproducibilità]

2. DESCRIZIONE DEL DATASET
   - N pazienti analizzati
   - Variabili incluse (con tipi)
   - Dati mancanti per variabile
   - Nota: "I dati sono stati anonimizzati prima dell'analisi"

3. CONTESTO CLINICO
   Riepilogo emerso dal dialogo di elicitazione
   (compilato dall'agente, confermato dal medico)

4. ANALISI — una sezione per ciascuna
   Per ogni analisi:
   - Motivazione: perché questa analisi per questa domanda
   - Metodo: spiegazione in linguaggio non tecnico
   - Risultati: grafici + tabelle + numeri chiave spiegati
   - Limiti statistici
   - [SPAZIO VUOTO] "Interpretazione clinica: ___________"
     (il medico scrive qui la propria interpretazione)

5. APPENDICE TECNICA
   - Parametri esatti di ogni analisi (per riproducibilità)
   - Software e versioni utilizzate
   - Nota metodologica

6. DISCLAIMER
   "Questo report è stato generato da ArchiMEDe a scopo di ricerca.
   L'interpretazione clinica dei risultati è responsabilità esclusiva
   del medico. ArchiMEDe non fornisce diagnosi né consigli terapeutici."
```

**Formato:** PDF con stile pulito e professionale. Generato server-side con
WeasyPrint o ReportLab (Python), inviato al client come file binario.

---

## 9. Billing e tiers

### Modello: pay-per-report con crediti

Il medico acquista crediti. Un credito = un report scaricato.
I crediti non scadono.

| Pacchetto | Crediti | Prezzo | Costo/report |
|---|---|---|---|
| Trial | 1 | €0 (registrazione) | — |
| Starter | 5 | €35 | €7 |
| Standard | 15 | €90 | €6 |
| Pro | 40 | €200 | €5 |

### Quando viene scalato il credito

Il credito viene scalato **al momento del download del report**, non durante
la conversazione. Se il medico abbandona la sessione prima di generare il report,
non paga nulla.

### Implementazione Stripe

- **Stripe Checkout** per l'acquisto dei pacchetti crediti (one-time payment)
- **Stripe Customer Portal** per storico acquisti e fatture
- I crediti vengono gestiti lato server (database utenti)
- Nessun dato di carta di credito transita per i nostri server

### Utenti istituzionali (futuro)

Per reparti o gruppi di ricerca: pacchetti custom con fatturazione istituzionale.
Fuori scope per MVP.

---

## 10. Privacy, GDPR e T&C

### Principi

- **Privacy-by-design:** nessun dato identificativo lascia il PC del medico
- **Data minimization:** il server riceve solo dati anonimi, necessari per l'analisi
- **Storage limitation:** sessioni eliminate dopo 4 ore di inattività
- **Hosting europeo:** obbligatorio per GDPR (dati sanitari = categoria speciale)

### Punti obbligatori nei T&C

1. ArchiMEDe è uno strumento per la ricerca clinica, non per decisioni diagnostiche
   o terapeutiche.
2. L'interpretazione clinica dei risultati è responsabilità esclusiva del medico.
3. Il medico è responsabile di caricare solo dati correttamente anonimizzati.
   ArchiMEDe esegue un best-effort di anonimizzazione automatica, ma non garantisce
   il rilevamento di tutti i dati identificativi.
4. I dati anonimizzati vengono trasmessi al server per l'elaborazione e eliminati
   entro 4 ore dalla fine della sessione.
5. ArchiMEDe non è un dispositivo medico certificato (MDR/CE).

### DPA (Data Processing Agreement)

Necessario con il provider LLM (Anthropic) per il trattamento di dati
potenzialmente sensibili. Anthropic offre DPA per clienti enterprise API.

---

## 11. Stack tecnico

| Layer | Tecnologia | Motivazione |
|---|---|---|
| Desktop app | Tauri (Rust + React) | Leggero, cross-platform, nessuna dipendenza per l'utente |
| Anonimizzazione locale | Microsoft Presidio (Python via sidecar) | Open source, gira in locale, specializzato in PII medico |
| Backend API | FastAPI (Python) | Asincrono, leggero, ottimo per LLM streaming |
| Session store | Redis con TTL | Veloce, eliminazione automatica per scadenza |
| Modello AI | Claude API (Anthropic) | Migliore per seguire istruzioni complesse e sfumate |
| Esecuzione codice | Sandbox Python isolato per sessione | Sicurezza: ogni utente ha il proprio ambiente |
| Report PDF | WeasyPrint o ReportLab | Generazione PDF da Python, nessuna dipendenza esterna |
| Billing | Stripe Checkout + Customer Portal | Standard di mercato, nessun dato carta sui nostri server |
| Hosting | AWS eu-west-1 o Hetzner DE | GDPR: hosting europeo obbligatorio per dati sanitari |
| Database utenti | PostgreSQL | Account, crediti, storico acquisti |

---

## 12. Roadmap

### Fase 0 — Proof of concept (già completato)
- [x] Pipeline di analisi statistica in Python (questo repo)
- [x] Blueprint agente con skills
- [x] Design architetturale dell'app

### Fase 1 — MVP (3-4 mesi)
- [ ] App Tauri con UI minimale (upload, chat, download)
- [ ] Presidio integrato per anonimizzazione dataset e messaggi
- [ ] Backend FastAPI con session store Redis
- [ ] Integrazione Claude API con system prompt base e skills MVP
- [ ] Analisi: descrittive, Spearman, confronto tra gruppi
- [ ] Report PDF base
- [ ] Stripe per acquisto crediti (pacchetto Starter e Standard)
- [ ] T&C e disclaimer di sessione
- [ ] Test con 2-3 medici pilota

### Fase 2 — Versione estesa (6-8 mesi)
- [ ] Analisi complete: LASSO, clustering, logistica
- [ ] Report PDF avanzato con grafici integrati
- [ ] Supporto SPSS e REDCap
- [ ] Memoria persistente tra sessioni (storico progetti)
- [ ] Pacchetto Pro e utenti istituzionali
- [ ] Audit delle conversazioni per affinare le guardrail

### Fase 3 — Scaling (12+ mesi)
- [ ] Certificazione MDR se richiesto dal mercato
- [ ] Integrazione con sistemi ospedalieri
- [ ] Compliance agent per contesti ad alto rischio
- [ ] Analisi avanzate: sopravvivenza, modelli misti, mediazione

---

*Questo documento è un blueprint di design. Tutte le scelte architetturali e tecniche
sono soggette a revisione in fase di implementazione sulla base dei test con utenti reali.*

*Documenti correlati:*
- *[AGENT_BLUEPRINT.md](AGENT_BLUEPRINT.md) — design dell'agente conversazionale*
- *[SKILLS_BLUEPRINT.md](SKILLS_BLUEPRINT.md) — skills operative dell'agente*
