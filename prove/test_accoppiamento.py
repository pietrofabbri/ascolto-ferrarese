#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""I test del patto fra le due repository.

Il difetto che questi test prendono è un **patto non scritto**: due repository
fratelli si passano dei dati con una riga di commento e un passo del workflow,
e nessuno dice quali file servono né quanto devono contenere. Il legame
invecchia in silenzio, ed è l'unico modo in cui due fratelli divergono senza
che nessuno lo veda.

Il secondo difetto è più sottile: il controllo passa anche quando **non può
guardare niente**. Se il repository fratello non c'è, `controlla` su una lista
vuota non trova problemi e dice che va tutto bene: un controllo che non parte è
un controllo che passa, ed è la cosa peggiore che ci sia.
"""
from __future__ import annotations

import io
import json
import os
import tempfile
import unittest

RADICE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
import sys  # noqa: E402
sys.path.insert(0, os.path.join(RADICE, "prove"))

import controlla_accoppiamento as modulo  # noqa: E402


def _fratello() -> str:
    d = modulo._fratello()
    if d:
        return d
    raise unittest.SkipTest("il repository fratello non c'è accanto: "
                            "il patto non si può controllare")


class _FratelloFinto(object):
    """Un fratello di prova, con dentro quello che il patto chiede."""
    def __init__(self, righe_aspettate=None, con_codice=True):
        self.cartella = tempfile.mkdtemp()
        for relativo, atteso in (righe_aspettate
                                 if righe_aspettate is not None
                                 else modulo.PATTO).items():
            numero = (atteso["righe"] if isinstance(atteso, dict) else atteso)
            self._scrivi(relativo, numero)
        for relativo in modulo.CODICE:
            percorso = os.path.join(self.cartella, relativo)
            os.makedirs(os.path.dirname(percorso), exist_ok=True)
            with io.open(percorso, "w", encoding="utf-8") as f:
                f.write("# finto\n")

    def _scrivi(self, relativo, numero):
        percorso = os.path.join(self.cartella, relativo)
        os.makedirs(os.path.dirname(percorso), exist_ok=True)
        with io.open(percorso, "w", encoding="utf-8") as f:
            f.write("// un commento, che non e' una riga\n")
            for i in range(numero):
                f.write(json.dumps({"id": "X%d" % i, "italiano": "parola%d" % i,
                                    "ferrarese": "parola%d" % i,
                                    "principale_italiano": "parola%d" % i})
                        + "\n")


class TestIlPattoFraLeDueRepository(unittest.TestCase):
    """Ogni file che questo repository legge, e quanto deve contenere."""

    def test_il_patto_e_dichiarato(self):
        for relativo in ("dati/fonetica.jsonl", "dati/glossario.jsonl",
                         "dati/coppie.jsonl", "dati/proverbi.jsonl"):
            self.assertIn(relativo, modulo.PATTO,
                          "%s e' letto ma non e' nel patto: e' un dato che "
                          "invecchiera' in silenzio" % relativo)
            self.assertTrue(modulo.PATTO[relativo]["serve_a"],
                            "%s e' nel patto senza dire a che cosa serve"
                            % relativo)

    def test_il_patto_torna_sul_fratello_vero(self):
        self.assertEqual(modulo.controlla(_fratello()), [],
                         "il patto non torna sul repository fratello")

    def test_un_file_che_mancsa_e_un_difetto(self):
        finto = _FratelloFinto()
        os.unlink(os.path.join(finto.cartella, "dati/proverbi.jsonl"))
        difetti = modulo.controlla(finto.cartella)
        self.assertTrue(difetti, "un file dichiarato che manca passa")
        self.assertIn("proverbi", " ".join(difetti))

    def test_un_numero_cambiato_e_un_difetto_e_dice_cosa_aggiornare(self):
        # Il numero che cambia e' la regola: se il fratello aggiunge una riga e
        # qui la dichiarazione resta, il patto mente in silenzio fino a una
        # misura che si comporta in modo inexplicable.
        attesi = dict(modulo.PATTO)
        attesi["dati/coppie.jsonl"] = {"righe": 99}
        finto = _FratelloFinto(attesi)
        difetti = modulo.controlla(finto.cartella)
        messaggi = " ".join(difetti)
        self.assertTrue(difetti, "un numero diverso passa: il patto e' una "
                                 "dichiarazione, non una promessa")
        self.assertIn("coppie.jsonl", messaggi)
        self.assertIn("aggiornata insieme", messaggi)

    def test_il_codice_del_fratello_e_nel_patto(self):
        # `legge` non e' un dato ma e' la regola di scrittura: senza, la misura
        # del cammino inverso non ha niente da percorrere.
        self.assertIn("sorgenti/traduttore/legge.py", modulo.CODICE)
        finto = _FratelloFinto()
        os.unlink(os.path.join(finto.cartella, "sorgenti/traduttore/legge.py"))
        difetti = modulo.controlla(finto.cartella)
        self.assertTrue(difetti)
        self.assertIn("legge", " ".join(difetti))

    def test_il_controllo_senza_il_fratello_non_passa(self):
        # Un controllo che non puo' guardare niente non deve dire che va bene:
        # il caso peggiore, e lo dichiara.
        finto = _FratelloFinto()
        os.unlink(os.path.join(finto.cartella, "dati/glossario.jsonl"))
        vecchio = os.environ.get("TRADUTTORE")
        os.environ["TRADUTTORE"] = os.path.join(finto.cartella, "non-c-e")
        try:
            self.assertIsNone(modulo._fratello())
            self.assertEqual(modulo.main(), 1,
                             "senza il fratello il controllo passa: e' il caso "
                             "peggiore")
        finally:
            if vecchio is None:
                os.environ.pop("TRADUTTORE", None)
            else:
                os.environ["TRADUTTORE"] = vecchio


class TestIlMaterialeDelVincolo(unittest.TestCase):
    """Che cosa il passo (2) ha su cui lavorare, e che cosa non può sapere.

    Il difetto che questi test prendono è il conteggio gonfiato: contando
    insieme le parole singole e le locuzioni, il vincolo di lessico sembra
    avere 17370 scelte quando ne ha 15585, e le 1785 locuzioni non sono una
    scelta possibile — sono sequenze, e se il vincolo ne risponde una a un
    suono sta inventando una frase.
    """

    def setUp(self):
        self.m = modulo.materiale(_fratello())

    def test_le_parole_e_le_locuzioni_sono_contate_separate(self):
        # La riga del file: una voce con piu' parole nell'italiano e' una
        # locuzione, e va contata fra le locuzioni.
        finto = _FratelloFinto()
        glossario = os.path.join(finto.cartella, "dati/glossario.jsonl")
        # «una parola» sarebbe una locuzione: due parole. Una voce di **una
        # parola sola** e' una voce come «cane», e il test che la chiama
        # «una parola» mentirebbe da solo.
        righe = [{"id": "A", "principale_italiano": "cane"},
                 {"id": "B", "principale_italiano": "due parole qua"},
                 {"id": "C", "italiano": "tre parole stesse qui"}]
        with io.open(glossario, "w", encoding="utf-8") as f:
            for riga in righe:
                f.write(json.dumps(riga) + "\n")
        m = modulo.materiale(finto.cartella)
        self.assertEqual(m["parole"], 1, "una voce di una parola sola")
        self.assertEqual(m["locuzioni"], 2,
                         "due voci di piu' parole, contate come locuzioni")

    def test_il_vincolo_sceglie_una_parola_e_non_una_frase(self):
        # Il numero che interessa e' `parole`, e da solo: e' fra quante il
        # passo (2) puo' scegliere davvero.
        self.assertGreater(self.m["parole"], 0)
        self.assertNotEqual(self.m["parole"],
                            self.m["parole"] + self.m["locuzioni"])

    def test_una_chiave_ambigua_e_un_difetto_da_dire(self):
        # Il caso reale: P0002 e P0003 hanno lo stesso italiano e due ferraresi
        # diversi. Non e' un errore del fratello, sono due rese della fonte, ma
        # chi deve scegliere non puo' farlo senza dirlo.
        finto = _FratelloFinto()
        proverbi = os.path.join(finto.cartella, "dati/proverbi.jsonl")
        righe = [{"id": "P1", "italiano": "Stessa frase qui",
                  "ferrarese": "prima resa"},
                 {"id": "P2", "italiano": "Stessa frase qui!",
                  "ferrarese": "seconda resa"}]
        with io.open(proverbi, "w", encoding="utf-8") as f:
            for riga in righe:
                f.write(json.dumps(riga) + "\n")
        m = modulo.materiale(finto.cartella)
        self.assertEqual(m["chiavi_ambigue"], 1,
                         "due proverbi con lo stesso italiano devono essere "
                         "un caso ambiguo")
        gruppo = list(m["ambigui"].values())[0]
        self.assertEqual(len(gruppo), 2)
        self.assertEqual([p["id"] for p in gruppo], ["P1", "P2"])

    def test_il_confronto_usa_la_stessa_chiave_del_fratello(self):
        # La regola e' scritta qui perche' non c'e' un posto comune, ed e' il
        # limite dichiarato: `chiave()` toglie accenti, punteggiatura e spazi.
        self.assertEqual(modulo._chiave("Non distinguere il baccello!"), "nondistinguereilbaccello")
        self.assertEqual(modulo._chiave("città"), "citta")
        self.assertEqual(modulo._chiave("l'a"), "la")


if __name__ == "__main__":
    unittest.main(verbosity=2)