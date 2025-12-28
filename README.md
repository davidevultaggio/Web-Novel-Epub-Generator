# Web Novel ePub Generator 📚

Questa è un'applicazione web costruita con Streamlit che permette di scaricare web novel e convertirle automaticamente in formato ePub.

## Funzionalità

- **Analisi URL**: Estrae automaticamente la lista dei capitoli dalla pagina indice di una novel.
- **Download Intelligente**: Scarica il contenuto pulito di ogni capitolo, rimuovendo pubblicità e script non necessari.
- **Conversione ePub**: Compila tutti i capitoli scaricati in un unico file ePub pronto per la lettura.
- **Interfaccia Semplice**: Facile da usare grazie all'interfaccia intuitiva.

## Compatibilità

> [!IMPORTANT]
> **Ottimizzato per Novelfull**: L'applicazione è stata sviluppata e testata principalmente per funzionare con il sito **Novelfull** (e siti con struttura simile).
>
> ⚠️ **Nota per altri siti**: Sebbene l'app tenti di adattarsi a diverse strutture HTML, il funzionamento su siti diversi da Novelfull **non è garantito** e potrebbe richiedere adattamenti specifici.

## Installazione

1. Assicurati di avere Python installato.
2. Clona questo repository o scarica i file.
3. Installa le dipendenze necessarie:

```bash
pip install -r requirements.txt
```

## Utilizzo

1. Avvia l'applicazione:

```bash
streamlit run app.py
```

2. Inserisci l'URL della pagina indice della novel (es. `https://novelfull.com/nome-novel.html`).
3. Clicca su **Analizza** per trovare i capitoli.
4. Una volta trovati i capitoli, clicca su **Scarica e Converti in ePub**.
5. Attendi il completamento del processo (una barra di avanzamento mostrerà il progresso).
6. Scarica il file ePub generato.

## Tecnologie

- **Streamlit**: Per l'interfaccia web.
- **Requests & BeautifulSoup**: Per il web scraping.
- **EbookLib**: Per la creazione dei file ePub.
