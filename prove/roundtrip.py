"""Il viaggio di andata e ritorno: quante parole sopravvivono?

Il progetto sa gia' andare dalla grafia al suono (`legge`, nel traduttore).
Qui si prova l'altro verso, e soprattutto si misura una cosa che nessuna
risposta puo' sostituire: **il cammino e' invertibile?**

La domanda non e' accademica. Un modello acustico generico, che non conosce
il ferrarese, produce per un suono una ipotesi approssimativa. A quel punto
la scelta della parola ferrarese la fa il lessico, e per passare dal suono
alla nostra grafia serve un cammino che non perda pezzi. Se il andata e
ritorno perde il suono, allora qualunque decodificatore costruito sopra
perdera' il suono, e non ha senso costruirlo.

Quindi il numero che esce da qui e' un **tetto**, non una promessa: e' la
migliore precisione che il nostro sistema di scrittura permette, prima ancora
di sapere se il modello acustico funziona. Se il numero e' alto, il vincolo
ha senso. Se e' basso, il primo problema non e' il modello: e' che non sappiamo
scrivere il ferrarese che ascoltiamo, e va risolto prima di comprare una
macchina.

Il confronto e' fatto symbol per symbol, togliendo il segno di accento e il
confine di sillaba: sono scelte della fonte, non suoni, e contarli come
differenze nasconderebbe il problema vero dietro un numero che sembra grave e
non lo e'.
"""

from __future__ import annotations

import json
import os
import sys

RADICE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RADICE, "sorgenti"))

from ascolto import rinomina as modulo          # noqa: E402

# Il traduttore e' un altro repository. Il legame e' dichiarato qui e basta:
# finche' non ci sara' un modo pulito di condividere le regole, i due
# confrontano i loro risultati e il numero dice se vanno d'accordo.
PERCORSO_FONETICA = os.path.join(
    os.path.dirname(RADICE), "traduttore-ferrarese", "dati", "fonetica.jsonl")


def _percorso_legge():
    """Il modulo `legge` del traduttore, se il repository c'e'."""
    percorso = os.path.join(os.path.dirname(RADICE), "traduttore-ferrarese",
                            "sorgenti")
    if not os.path.isdir(percorso):
        return None
    sys.path.insert(0, percorso)
    try:
        from traduttore import legge
        return legge
    except ImportError:
        return None


def _spogli(ipa: str) -> str:
    """La IPA senza accento e senza confini di sillaba: solo i suoni."""
    return ipa.replace("ˈ", "").replace("ɡ", "g").strip("/")


def _trascrizioni(percorso: str) -> list:
    righe = []
    with open(percorso, encoding="utf-8") as f:
        for riga in f:
            riga = riga.strip()
            if not riga or riga.startswith("//"):
                continue
            righe.append(json.loads(riga))
    return righe


def main() -> int:
    legge = _percorso_legge()
    if not os.path.isfile(PERCORSO_FONETICA) or legge is None:
        print("Non trovo il repository traduttore-ferrarese accanto a questo.")
        print("Il confronto ha bisogno delle sue regole di lettura: senza")
        print("quelle non c'e' nessun andata e ritorno da misurare.")
        return 1

    righe = _trascrizioni(PERCORSO_FONETICA)
    stesse = 0
    suoni_persi = 0
    non_riconosciute = 0
    dettaglio = []

    for t in righe:
        forma, ipa = t.get("forma", ""), t.get("ipa", "")
        if not forma or not ipa:
            continue
        rinominata = modulo.rinomina(ipa)
        if not rinominata.get("completa", True):
            non_riconosciute += 1
            dettaglio.append("  %-12s %-16s non scrivibile: %s"
                             % (t.get("id"), ipa,
                                (rinominata["dubbi"] or ["?"])[0][:70]))
            continue
        if not rinominata["forma"]:
            non_riconosciute += 1
            dettaglio.append("  %-12s %-16s non scrivibile: %s"
                             % (t.get("id"), ipa, rinominata["dubbi"][:1]))
            continue
        riletta = legge.leggi(rinominata["forma"])["ipa"]
        if _spogli(riletta) == _spogli(ipa):
            stesse += 1
            if rinominata["forma"] == forma:
                dettaglio.append("  %-12s %-14s -> %-14s stessa scrittura"
                                 % (t.get("id"), forma, rinominata["forma"]))
            else:
                dettaglio.append("  %-12s %-14s -> %-14s scrittura diversa, "
                                 "stesso suono"
                                 % (t.get("id"), forma, rinominata["forma"]))
        else:
            suoni_persi += 1
            dettaglio.append("  %-12s %-16s -> %-14s -> %-16s  SUONO DIVERSO"
                             % (t.get("id"), ipa, rinominata["forma"], riletta))

    totale = stesse + suoni_persi + non_riconosciute
    print("VIAGGIO DI ANDATA E RITORNO")
    print()
    for riga in dettaglio:
        print(riga)
    print()
    print("trascrizioni considerate        %d" % totale)
    print("suono conservato               %d" % stesse)
    print("suono perso                    %d" % suoni_persi)
    print("non scrivibili                 %d" % non_riconosciute)
    if totale:
        print("copertura del suono            %.0f%%"
              % (100.0 * stesse / totale))
    return 0


if __name__ == "__main__":
    sys.exit(main())