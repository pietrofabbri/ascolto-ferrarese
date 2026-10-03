---
titolo: Ascolto ferrarese
versione: 0.1
data: 2026-10-03
autore: progetto «I cinque duchi»
---

# Ascolto ferrarese

Un sistema che **capisce** il ferrarese parlato. Non esiste ancora, e questo
repository dice perché non può esistere ancora, cosa manca, e cosa si può
cominciare a costruire **oggi** senza avere ancora quei pezzi.

Repository fratello di [`traduttore-ferrarese`](../traduttore-ferrarese), che
traduce fra italiano e ferrarese scritto. Qui si ragiona sul ferrarese **detto**.

## La risposta corta, prima di tutto

**Non c'è audio ferrarese.** Nel repository del traduttore,
`dati/audio.jsonl` è vuoto, ed è vuoto per una decisione dichiarata: quel
file elenca le persone che hanno parlato e che cosa hanno detto, e nessuna ha
ancora parlato.

Questo cambia l'ordine delle cose. Un modello acustico generico — Whisper o
qualunque altro — non impara una lingua da zero: riconosce quella che ha già
sentito. Il ferrarese non c'è nei suoi dati di addestramento, quindi su una
frase ferrarese produrrà qualcosa che **sembra** italiano, con parole italiane
al posto giusto e il ritmo sbagliato. Non fallirà: **farà finta**, e quella è
la parte pericolosa.

Quindi la prima cosa da costruire non è il modello. È la misura.

## Come dovrebbe essere fatto, e perché in quest'ordine

```
microfono
   │
   ├─ (1) modello acustico ──► suono approssimativo, con i tempi
   │        ↑ non conosce il ferrarese: è un generico, e va detto
   │
   ├─ (2) VINCOLO DI LESSICO ──► la parola ferrarese che meglio ci sta
   │        ↑ qui sta tutto il ferrarese: è nostro, non del modello
   │
   ├─ (3) ASTENSIONE ──► «non l'ho capito», quando il passo 2 è debole
   │
   └─ (4) il motore del traduttore ──► italiano
```

Il punto che regge tutto: **il modello non sa niente di ferrarese, e non deve
saperlo.** Il passo 2 è l'unico che ha bisogno di conoscere il dialetto, e quel
passo è interamente nostro — è il glossario, sono le regole di scrittura, sono
i proverbi. Un modello fine-tuned su poche ore di ferrarese rischierebbe di
diventare *peggiore* di un modello generico vincolato, perché avrebbe visto
troppo poco per generalizzare e avrebbe imparato il modo di parlare di chi ha
registrato per primo.

Il passo 3 non è un dettaglio. Una lingua che ha perso metà del suo lessico
non può essere ricostruita a mano da una macchina che indovina: quello che
produce è **ferrarese inventato**, cioè l'illusione più dannosa che si possa
fare a un dialetto. Meglio una frase con tre parole fuori e un «non l'ho
capito» che una frase intera, per metà giusta e per metà inventata, che
nessuno ha detto e che suona come se l'avesse detto.

## Il primo passo, fatto: il cammino inverso è misurabile

Perché il passo 2 funzioni serve una mappa **dal suono alla nostra grafia**.
Non è il rovescio di quella che già esiste: quella (nel traduttore, modulo
`legge`) va dalla grafia al suono, e la si usa per far suonare le parole. Qui
serve l'altro verso, e per costruirlo ho fatto la misura più onesta
possibile senza audio e senza modelli.

`prove/roundtrip.py` prende le 28 trascrizioni del traduttore, le fa
andare suono → grafia → suono, e conta quante sopravvivono.

```
trascrizioni considerate        28
suono conservato               27
suono perso                    0
non scrivibili                 1
copertura del suono            96%
```

Il 96% è un **tetto**, non una promessa: è la migliore precisione che il
nostro sistema di scrittura permette, prima ancora di sapere se il modello
acustico funziona. Se il numero fosse basso, il primo problema non sarebbe il
modello: sarebbe che non sappiamo scrivere il ferrarese che ascoltiamo, e
quello va risolto prima di comprare qualunque macchina.

L'unico caso non scrivibile è dichiarato, non risolto: `/ɲ/` davanti a
consonante (`magnàr` = /maˈɲnar/) non è prodotto da nessuna grafia che il
progetto conosca. Il modulo si ferma e lo dice.

## Che cosa ha già trovato la misura

Costruendo il cammino inverso sono usciti due difetti **veri** nel motore del
traduttore, che stava in guardia da una versione:

- **`nag` leggeva `/nadʒ/` e `mang` `/mandʒ/`**, perché in Python la stringa
  vuota è sottostringa di qualunque stringa: `"" in "eie"` è vero, e ogni `c`
  o `g` finale di parola diventava affricata.
- **`gì` leggeva `/g/` invece di `/dʒ/`**, perché la lista delle vocali
  anteriori era la stringa `"eieèi"` e mancavano `ì` e `í`.

Entrambi corretti e coperti da test. Nessuno dei due si sarebbe trovato
leggendo il codice: sono usciti facendo una misura che non esisteva.

## Cosa serve davvero, in ordine

1. **Un protocollo di registrazione.** Poche decine di minuti di parlante
   ferrarese, con consenso scritto, e la trascrizione fatta da due persone.
   Non serve un corpus: serve una **riga di base** e una misura di errore.
   Senza questo, tutto il resto è un paragone senza metro.
2. **Il piccolo set di valutazione.** Frasi brevi, con la risposta che si
   aspetta. È l'unico modo per sapere se «capisce» è una parola o una
   speranza.
3. **Solo dopo, il modello.** E a quel punto si valuta se il vincolo di
   lessico batte il modello generico da solo: se non lo batte, il passo 2 non
   serve e l'hanno fatta lunga per niente.

## Regole, ereditate dal progetto

Nessuna risposta senza fonte. Nessun vuoto riempito a caso. I controlli
segnalano, non correggono. Nessun dato di studente. Nessuna rete a runtime.
Codice MIT, dati con licenza dichiarata per voce.

La regola che qui pesa di più è l'ultima dell'elenco di `AGENTS.md`: **chi non
sa, dice che non sa.** Un sistema che ascolta il ferrarese e non ammette di non
capire è peggio di un sistema che non esiste, perché chi lo usa non ha più il
modo di accorgersene.

## Cosa c'è dentro

- `sorgenti/ascolto/rinomina.py` — il cammino dal suono alla grafia, che
  dichiara i dubbi invece di sciogliere le ambiguità a caso.
- `prove/roundtrip.py` — la misura. È la parte che rende tutto il resto
  verificabile.
- `prove/test_rinomina.py` — i test.

Nessuna dipendenza, nessuna rete, nessun modello: qui si ragiona sulla scrittura.