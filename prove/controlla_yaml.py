"""Verifica i blocchi Python del workflow.

Su questa macchina non c'e' PyYAML, quindi il file di workflow non puo' essere
validato come YAML. Quello che si puo' fare, e che e' la parte che sbaglia piu'
volte, e' controllare che i **blocchi di codice dentro** il file siano Python
valido: uno script dentro uno YAML non e' YAML, e un errore di sintassi li'
dentro fallisce solo al momento di girare, in CI, su un altro computer.

Questo script esiste perche' un controllo che non parte non e' un controllo che
passa, anche per i controlli dei controlli.
"""

from __future__ import annotations

import io
import os
import re
import sys
import textwrap

RADICE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PERCORSO = os.path.join(RADICE, ".github", "workflows", "verifica.yml")

# I blocchi dentro un `run: |` sono indentati, e l'indentazione e' di YAML: lo
# YAML la toglie prima di passare il testo alla shell. Per compilarli qui va
# tolta come farebbe lui, altrimenti si legge un errore di indentazione che
# sul serio non c'e'.
TITOLI = r"<<'PY2?'"
CHIUSURE = r"\n *PY2?"


def blocchi(testo: str) -> list:
    return [textwrap.dedent(b) for b in re.findall(TITOLI + r"\n(.*?)" + CHIUSURE,
                                                    testo, re.S)]


def main() -> int:
    if not os.path.isfile(PERCORSO):
        print("non c'e' il workflow, e va bene: niente da controllare")
        return 0
    testo = io.open(PERCORSO, encoding="utf-8").read()
    trovati = blocchi(testo)
    if not trovati:
        print("ERRORE: nessun blocco Python nel workflow. Il workflow doveva")
        print("        controllare qualcosa e non controlla niente.")
        return 1
    sbagliati = 0
    for indice, sorgente in enumerate(trovati, 1):
        try:
            compile(sorgente, "<blocco %d>" % indice, "exec")
            print("  blocco %d: sintassi ok" % indice)
        except SyntaxError as errore:
            sbagliati += 1
            print("  blocco %d: %s alla riga %s" % (indice, errore.msg,
                                                    errore.lineno))
    if sbagliati:
        print("ERRORE: %d blocchi su %d non sono Python valido" % (sbagliati,
                                                                    len(trovati)))
        return 1
    print("%d blocchi Python, tutti validi" % len(trovati))
    return 0


if __name__ == "__main__":
    sys.exit(main())