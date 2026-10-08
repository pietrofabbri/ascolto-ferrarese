#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Che cosa questo repository chiede al fratello, e che cosa il fratello gli dà.

**Il buco che questo controllo chiude.** Fra i due repository c'è un legame
dichiarato in una riga di un commento e in un passo del workflow: si clona
`traduttore-ferrarese` e se ne leggono `dati/fonetica.jsonl` e il modulo `legge`.
Tutto il resto è un patto non scritto: nessuno dice **quali** file servono,
**quanto** devono contenere, e **che cosa** di quei dati è davvero materiale
per il passo (2) di questa architettura. Il legame, così, invecchia in
silenzio: il fratello aggiunge un file, questo repository continua a passarlo
come se non ci fosse, e nessuno se ne accorge fino a una misura che si
comporta in modo inspiegabile.

Quindi qui il patto è **scritto**, con i numeri accanto:

- ogni file che questo repository legge è dichiarato, e se manca è un errore
  — un controllo che non parte non è un controllo che passa;
- ogni file dichiarato ha un **conteggio atteso**, e se cambia è un errore con
  il messaggio che dice che cosa aggiornare. È la stessa regola del tetto del
  96%: non si può far scendere un numero dichiarato in silenzio;
- il **materiale** del vincolo di lessico viene misurato e dichiarato, perché un
  vincolo che non sa quanto materiale ha è un vincolo che non può dichiarare
  quando deve astenersi.

Uso:
    python3 prove/controlla_accoppiamento.py

Il repository fratello si cerca nella directory accanto, o dove dice la
variabile d'ambiente `TRADUTTORE`.
"""
from __future__ import annotations

import collections
import io
import json
import os
import sys

RADICE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _fratello() -> str:
    """Il repository fratello, o `None` se da nessuna parte."""
    dichiarato = os.environ.get("TRADUTTORE")
    if dichiarato:
        return dichiarato if os.path.isdir(dichiarato) else None
    vicino = os.path.join(os.path.dirname(RADICE), "traduttore-ferrarese")
    return vicino if os.path.isdir(vicino) else None


# Il patto. `righe` è il numero atteso di righe di dati: se cambia, la
# dichiarazione di questo repository va aggiornata **insieme** alla modifica,
# e l'errore dice quale numero.
PATTO = {
    "dati/fonetica.jsonl": {"righe": 28,
                            "serve_a": "la misura del cammino inverso"},
    "dati/glossario.jsonl": {"righe": 17370,
                             "serve_a": "il materiale del vincolo di lessico"},
    "dati/coppie.jsonl": {"righe": 48,
                          "serve_a": "il materiale del vincolo di lessico"},
    "dati/proverbi.jsonl": {"righe": 28,
                            "serve_a": "il materiale del vincolo di lessico, "
                                       "le frasi intere"},
}
# Anche i file che non sono dati: il modulo `legge` è la regola di scrittura,
# e senza quella regola la misura del cammino inverso non ha niente da
# percorrere.
CODICE = ["sorgenti/traduttore/legge.py"]


def _righe(percorso: str) -> list:
    """Le righe di dati di un file jsonl, senza i commenti."""
    out = []
    with io.open(percorso, encoding="utf-8") as f:
        for riga in f:
            riga = riga.strip()
            if riga and not riga.startswith("//"):
                out.append(json.loads(riga))
    return out


def _chiave(testo: str) -> str:
    """La chiave di confronto, con la stessa regola del fratello.

    Il fratello toglie accenti, punteggiatura e spazi prima di confrontare, e
    qui si fa lo stesso: due scritture diverse dello stesso proverbio sono la
    stessa frase. **La regola è scritta qui perché non c'è un posto comune**
    dove metterla, ed è il limite dichiarato di due repository fratelli che non
    si condividono il codice. Se un giorno il fratello cambiasse la sua, qui
    il numero cambierebbe e nessuno se ne accorgerebbe: è il patto che questo
    controllo dichiara.
    """
    import unicodedata
    testo = unicodedata.normalize("NFKD", (testo or "").lower())
    testo = "".join(c for c in testo if not unicodedata.combining(c))
    return "".join(c for c in testo if c.isalnum())


def controlla(fratello: str) -> list:
    """I difetti del patto. lista vuota = il patto è a posto."""
    difetti = []
    for relativo, atteso in sorted(PATTO.items()):
        percorso = os.path.join(fratello, relativo)
        if not os.path.exists(percorso):
            difetti.append("manca %s: %s serve a %s, e senza quella riga non "
                           "c'è niente da controllare"
                           % (relativo, relativo, atteso["serve_a"]))
            continue
        righe = _righe(percorso)
        if len(righe) != atteso["righe"]:
            difetti.append(
                "%s ha %d righe e la dichiarazione di questo repository ne "
                "dice %d: la dichiarazione va aggiornata insieme alla "
                "modifica, non dopo" % (relativo, len(righe), atteso["righe"]))
    for relativo in CODICE:
        if not os.path.exists(os.path.join(fratello, relativo)):
            difetti.append("manca %s: è la regola di scrittura, e senza quella "
                           "non c'è cammino inverso da misurare" % relativo)
    return difetti


def materiale(fratello: str) -> dict:
    """Che cosa il vincolo di lessico ha su cui lavorare.

    Tre numeri, e i tre sono limiti:

    - **parole singole**: voci del glossario fatte di una parola sola. È il
      materiale di cui il passo (2) ha bisogno davvero, perché sceglie **una**
      parola per un suono: un glossario di locuzioni non aiuta a scegliere
      niente;
    - **locuzioni**: voci di più parole. Servono al modello di linguaggio, non
      al vincolo, e contate insieme alle altre farebbero sembrare il vincolo
      più ricco di quanto sia;
    - **frasi intere**: coppie e proverbi. Qui comincia il problema dichiarato
      in `AGENTS.md`: se il modello ipotizza una sequenza e noi rispondiamo con
      una frase intera senza dire che era una delle poche, il sistema fa finta.
    """
    glossario = _righe(os.path.join(fratello, "dati/glossario.jsonl"))
    parole = locuzioni = 0
    for voce in glossario:
        principale = (voce.get("principale_italiano")
                      or voce.get("italiano") or "")
        if " " in principale.strip():
            locuzioni += 1
        else:
            parole += 1

    coppie = _righe(os.path.join(fratello, "dati/coppie.jsonl"))
    proverbi = _righe(os.path.join(fratello, "dati/proverbi.jsonl"))

    # L'ambiguità dichiarata: due proverbi con lo stesso italiano e due
    # ferraresi diversi. Non è un difetto del fratello — sono due rese della
    # fonte — ma per chi deve scegliere è un caso in cui **non si può scegliere
    # senza dirlo**, ed è la prima volta che il progetto misura un
    # schieramento di questo tipo.
    per_chiave = collections.defaultdict(list)
    for proverbio in proverbi:
        per_chiave[_chiave(proverbio.get("italiano", ""))].append(proverbio)
    ambigui = {k: v for k, v in per_chiave.items() if len(v) > 1}

    return {
        "parole": parole,
        "locuzioni": locuzioni,
        "coppie": len(coppie),
        "proverbi": len(proverbi),
        "frasi_intere": len(per_chiave),
        "chiavi_ambigue": len(ambigui),
        "ambigui": ambigui,
    }


def main() -> int:
    fratello = _fratello()
    if fratello is None:
        print("ERRORE: il repository fratello `traduttore-ferrarese` non c'è "
              "accanto a questo, e la variabile TRADUTTORE non dice dove è.")
        print("Il patto fra i due repository è dichiarato in "
              "`prove/controlla_accoppiamento.py`: se il fratello non c'è, "
              "questo controllo non ha niente da dire e non può passare.")
        return 1

    difetti = controlla(fratello)
    for difetto in difetti:
        print("difetto  %s" % difetto)
    if difetti:
        print()
        print("Il patto fra i due repository non torna. Se la modifica è "
              "giusta, la dichiarazione va aggiornata **nello stesso "
              "commit**, e il numero da correggere è quello del file detto.")
        return 1

    m = materiale(fratello)
    print("il materiale del vincolo di lessico")
    print("  parole singole nel glossario   %5d   il materiale del passo (2)" % m["parole"])
    print("  locuzioni nel glossario        %5d   utili al modello, non al "
          "vincolo" % m["locuzioni"])
    print("  coppie (frasi intere)          %5d" % m["coppie"])
    print("  proverbi                       %5d   %d chiavi italiane distinte"
          % (m["proverbi"], m["frasi_intere"]))
    print("  chiavi con piu' di una resa    %5d   casi in cui non si puo' "
          "scegliere senza dirlo" % m["chiavi_ambigue"])
    print()
    print("Il vincolo puo' scegliere fra %d parole; gli altri %d dati sono "
          "frasi." % (m["parole"], m["coppie"] + m["frasi_intere"]))
    if m["chiavi_ambigue"]:
        print("Casi ambigui, per intero:")
        for chiave, gruppo in sorted(m["ambigui"].items()):
            for proverbio in gruppo:
                print("  %s  %s → %s" % (proverbio.get("id", "?"),
                                        proverbio.get("italiano", "")[:58],
                                        proverbio.get("ferrarese", "")))
    return 0


if __name__ == "__main__":
    sys.exit(main())