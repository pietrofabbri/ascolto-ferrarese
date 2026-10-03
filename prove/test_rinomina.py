"""I test del cammino dal suono alla grafia.

Non si testa che il modulo «funziona»: si testa che **non inventa**. Ogni test
qui blocca un modo in cui un suono potrebbe diventare una scrittura che nessuno
ha scritta, e ogni commento dice perché quella scrittura sarebbe un falso.
"""

from __future__ import annotations

import os
import sys
import unittest

RADICE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RADICE, "sorgenti"))

from ascolto.rinomina import rinomina, scelta_esplicita  # noqa: E402


def _nudata(testo):
    """Il testo senza i segni diacritici: la lettera vera, senza la marca."""
    import unicodedata
    decomposed = unicodedata.normalize("NFD", testo)
    return "".join(c for c in decomposed
                   if unicodedata.category(c) != "Mn")


class TestRinomina(unittest.TestCase):

    def test_una_parola_senza_dubbi_si_scrive(self):
        # I casi che il sistema sa risolvere. Qui non si cerca la perfezione:
        # si verifica che la via normale produca una grafia e la dichiari
        # completa, e non un mezzo risultato presentato come se fosse tutto.
        for ipa, atteso in (("/brisa/", "brisa"), ("/ka/", "ca"),
                            ("/pan/", "pan"), ("/majˈal/", "majàl"),
                            ("/vera/", "vera")):
            esito = rinomina(ipa)
            self.assertEqual(esito["forma"], atteso, ipa)
            self.assertTrue(esito["completa"], ipa)

    def test_la_s_e_la_z_restano_un_dubbio_e_non_una_scelta(self):
        # Il buco centrale della lingua: la regola 6 dichiara che `s` e `z` si
        # leggono come sono scritte e che questo NON e' una regola. Scrivere
        # una delle due e passare come se fosse stata scelta produrrebbe
        # ferrarese inventato, che e' la cosa che questo progetto non fa.
        esito = rinomina("/briˈsa/")
        self.assertTrue(esito["dubbi"], "il dubbio su s e z deve restare")
        self.assertIn("z", esito["alternative"])

    def test_chi_ha_ascoltato_puo_chiudere_il_dubbio(self):
        # E' il punto in cui il modulo serve una persona vera. Senza la sua
        # risposta la funzione non scrive niente: un `None` e' piu' utile di
        # una parola inventata, e il chiamante puo' distinguerli.
        self.assertIsNone(scelta_esplicita("/briˈsa/"))
        scelta = scelta_esplicita("/briˈsa/", scegliere_s="z")
        self.assertIsNotNone(scelta)
        self.assertIn("z", scelta)

    def test_una_sillaba_accentata_si_scrive_su_una_vocale(self):
        # Difetto preso dalla misura: in `/fraˈrɛs/` il segno sta sulla `r` e la
        # vocale accentata arriva dopo. Se l'accento non viaggia, la vocale
        # viene scritta senza accento e la parola cambia suono.
        self.assertEqual(rinomina("/fraˈrɛs/")["forma"], "frarès")
        self.assertEqual(rinomina("/ˈfrara/")["forma"], "fràra")

    def test_la_g_velare_davanti_a_vocale_anteriore_si_scrive_gh(self):
        # Scrivere `ge` produrrebbe /dʒe/, che e' un altro suono: la regola 4
        # rende palatali `c` e `g` davanti a vocale anteriore, e il modo per
        # evitarlo e' proprio il digramma.
        self.assertEqual(rinomina("/ɡe/")["forma"], "ghe")
        self.assertEqual(rinomina("/ɡi/")["forma"], "ghi")

    def test_la_g_vela_davanti_a_vocale_posteriore_si_scrive_g(self):
        # Il caso opposto, perche' e' quello che va storto se si generalizza:
        # davanti ad `a` la `g` resta velare e non vuole il digramma.
        self.assertEqual(rinomina("/ga/")["forma"], "ga")

    def test_un_suono_ignoto_si_dichiara_e_non_si_scrive_a_caso(self):
        esito = rinomina("/sɑmɛ/")
        self.assertFalse(esito["completa"])
        # Il messaggio puo' non essere il primo: in `/sɑmɛ/` il dubbio su `s`
        # e `z` viene prima di quello sul simbolo sconosciuto, ed e' giusto che
        # vengano segnalati entrambi e in quell'ordine.
        self.assertTrue(any("non si scrive a caso" in d
                            for d in esito["dubbi"]), esito["dubbi"])
        self.assertTrue(any("ɑ" in d for d in esito["dubbi"]),
                        esito["dubbi"])

    def test_la_nasale_palatale_davanti_a_consonante_non_si_scrive(self):
        # Il caso dichiarato, non risolto. `magnar` = /maˈɲnar/ nella fonte, e
        # nessuna grafia del progetto produce /ɲ/ davanti a consonante: o la
        # palatale raddoppia, o manca una regola. Scrivere `gnn` sarebbe
        # inventare una parola che nessuno ha scritta mai.
        esito = rinomina("/maˈɲnar/")
        self.assertFalse(esito["completa"], "non si deve dichiarare completo")
        self.assertTrue(any("ɲ" in d for d in esito["dubbi"]), esito["dubbi"])

    def test_il_vuoto_e_il_cilentono(self):
        self.assertFalse(rinomina("")["completa"])
        self.assertFalse(rinomina("   ")["completa"])
        self.assertFalse(rinomina("/")["completa"])

    def test_nessuna_scrittura_e_inventata(self):
        # Ogni grafia prodotta deve contenere solo lettere che questo dialetto
        # scrive. Una lettera fuori da qui significa che il modulo ha aperto
        # una parentesi e non l'ha chiusa.
        for ipa in ("/brisa/", "/majˈal/", "/ɡe/", "/tʃina/", "/prinˈtʃipar/"):
            for forma in ([rinomina(ipa)["forma"]] + rinomina(ipa)["alternative"]):
                if not forma:
                    continue
                # Gli accenti sono parte della grafia ferrarese (`majàl`), e
                # sono anche le marche toniche che questo modulo sceglie fra
                # due senza saper quale sia giusta. Quindi si confronta la
                # lettera nuda, e le marche si controllano a parte.
                for carattere in _nudata(forma.lower()):
                    self.assertIn(carattere, "abcdefghijklmnopqrstuvxz",
                                  "%s: %r" % (ipa, forma))
                for carattere in forma.lower():
                    if carattere.isalpha():
                        self.assertIn(carattere,
                                      "abcdefghijklmnopqrstuvxzàéíìóòùú",
                                      "%s: %r" % (ipa, forma))


if __name__ == "__main__":
    unittest.main(verbosity=2)