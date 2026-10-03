"""Dal suono alla grafia ferrarese: il cammino che a nessuno serve finora').

`traduttore-ferrarese` sa andare dalla **grafia al suono**: conosce le regole di
lettura dichiarate in `dati/fonetica.jsonl` e le applica a `magnàr` per ottenere
`/magnˈar/`. Quel cammino e' adesso usato ogni volta che si vuole far
suonare una parola.

Qui si fa il cammino **opposto**, e nasce per una ragione precisa: se un giorno
qualcuno vuole un sistema che *capisce* il ferrarese parlato, la prima cosa che
quel sistema deve fare non e' capire: e' **trascrivere**. E per trascrivere con
un modello acustico generico, che non conosce il ferrarese e lo accosta
all'italiano, la parte che conta non e' il modello: e' il vincolo. Si lascia
il modello dire «suono approssimativo» e poi si sceglie la parola **ferrarese**
che meglio ci sta, usando il glossario e queste regole.

Per fare quel lavoro serve una mappa dal suono alla nostra grafia. Non e' il
rovescio di quella che gia' c'e'. Il punto e' questo, ed e' il punto di tutto
il modulo: **una grafia ferrarese non si ricostruisce univocamente dal
suono**, e non perche' lo strumento sia scarso. `/s/` puo' essere `s` o `z`;
una vocale tonica /ɛ/ puo' venire da `è` o da `é`; una /a/ tonica da `à` o da
`á`. Sono scelte della fonte, e nessuna fonte che il progetto conosce le ha
dichiarate per questi casi.

Quindi questo modulo non restituisce una risposta sola. Restituisce:

- `forma`: la scrittura **piu' probabile**, secondo le regole dichiarate;
- `alternative`: le altre scritture equally compatibili con lo stesso suono;
- `dubbi`: le scelte che nessuna fonte ha dichiarato, una per una.

E la cosa che conta di piu': quando il suono non basta a scegliere, il modulo
**non sceglie**. Un sistema che ascolta il ferrarese e produce una frase ferrarese
sembravole ma sbagliata e' il modo peggiore di esistere per una lingua che ha
perso mezzo lessico: sembra che il dialetto ci sia ancora, e invece si e'
inventata roba nuova. Meglio «non l'ho capito», che e' una risposta vera.

Le regole sono le stesse di `traduttore-ferrarese`, prese dal file che le
dichiara. Qui sono riscritte al contrario e sono tenute allineate a mano: le due
copie sono controllate l'una contro l'altra da `prove/roundtrip.py`, che
riporta il numero di parole che sopravvivono al viaggio di andata e ritorno. Se
 quel numero scende, vuol dire che le due copie hanno smesso di dirsi la stessa
cosa, e il numero e' la prova.

Nessuna dipendenza, nessuna rete, nessun modello: qui si ragiona sulla scrittura.
Il modello acustico e' un'altra faccenda, e arriva dopo, se arriva.
"""

from __future__ import annotations

# Le vocali toniche: dal suono alla lettera accentata. Il sistema non sa
# dire quale delle due marche sia giusta per una data fonte, quindi ne
# restituisce due e lo dichiara. Non e' un dettaglio: `è` ed `e'`
# nell'Ottocento non sono la stessa scelta, e scegliere a caso fabbricherebbe
# una grafia che nessuno ha scritto.
VOCALI_TONICHE = {
    "a": ("à", "á"),
    "ɛ": ("è", "é"),
    "i": ("ì", "í"),
    "o": ("ò", "ó"),
    "u": ("ù", "ú"),
}

# Le vocali non toniche si scrivono senza accento.
VOCALI = {"a": "a", "ɛ": "e", "e": "e", "i": "i", "o": "o", "u": "u"}

# Le consonanti lette come si scrivono. La `j` e' il caso particolare: in
# questa fonte e' una semivocale (`majàl` = /majˈal/), e quindi si scrive
# `j`, non `i`.
CONSONANTI = {
    "b": "b", "d": "d", "f": "f", "k": "c", "g": "g", "l": "l",
    "m": "m", "n": "n", "p": "p", "r": "r", "t": "t", "v": "v",
    "j": "j", "ɲ": "gn",
}

# I simboli che non si scrivono con una lettera sola. Il valore e' una
# coppia: consonante, vocale. La vocale serve perche' in italiano la `c`
# cambia valore a seconda di quello che viene dopo (`c` + `i` = /tʃi/,
# `c` + `a` = /ka/), e in ferrarese lo stesso. Quindi la scrittura di
# /tʃ/ non e' `c`: e' `ci`, `ce` o `cia` secondo la vocale che segue.
AFFRICATE = {"tʃ": "c", "dʒ": "g"}

# Le due lettere che si somigliano e che il progetto non sa distinguere.
# La regola 6 di `dati/fonetica.jsonl` dichiara che `s` e `z` si leggono
# «come sono scritte» e che questo non e' una regola ma una scelta che puo'
# essere sbagliata: qui la scelta si propaga e diventa una **ambiguitita'**
# di scrittura. Non e' un dettaglio da sistemare piu' avanti, e' il buco
# centrale della lingua, ed e' dichiarato come tale.
S_E_Z = {"s": ("s", "z"), "z": ("z", "s")}

# Il segno di accento nella IPA non e' un suono: dice quale sillaba e' tonica.
ACCENTO = "ˈ"

# I simboli IPA che questo modulo sa scrivere. Se ne arrivasse uno che non
# c'e' qui, il modulo si ferma e lo dice: una scrittura inventata per un
# suono non capito e' la peggiore delle risposte.
SIMBOLI_NOTI = (set(VOCALI) | set(CONSONANTI) | set(AFFRICATE)
                | set(S_E_Z) | {"\u0261"})


def _scansiona(ipa: str) -> tuple:
    """La IPA in pezzi `(simbolo, tonica)`.

    Tonica vuol dire «porta il segno di accento», non «e' tonica»: il segno
    puo' stare davanti a una consonante, come in `/maˈɲnar/`, dove la vocale
    della sillaba accentata arriva dopo. Quindi il segno viaggia col pezzo e
    viene usato quando si incontra la vocale, che e' il vero nucleo.
    """
    pezzi = []
    accento_in_attesa = False
    resto = ipa.strip("/")
    i = 0
    while i < len(resto):
        if resto[i] == ACCENTO:
            accento_in_attesa = True
            i += 1
            continue
        if resto.startswith("tʃ", i):
            pezzi.append(("tʃ", accento_in_attesa))
            i += 2
        elif resto.startswith("dʒ", i):
            pezzi.append(("dʒ", accento_in_attesa))
            i += 2
        else:
            pezzi.append((resto[i], accento_in_attesa))
            i += 1
        accento_in_attesa = False
    return pezzi


def rinomina(ipa: str) -> dict:
    """La grafia ferrarese che meglio corrisponde a questa IPA.

    Ritorna sempre un dizionario. Quando non si puo' scegliere, `forma` e' la
    prima delle scelte possibili, `alternative` contiene le altre, e `dubbi`
    spiega perche' la scelta non e' una. Il chiamante puo' cosi' fare due
    cose diverse con lo stesso risultato: mostrare la parola, oppure
    rifiutarsi di indovinare.
    """
    esito = {
        "ipa": ipa,
        "forma": "",
        "alternative": [],
        "dubbi": [],
        "attendibilita": "I",
        "completa": True,
    }
    if not (ipa or "").strip():
        esito["dubbi"].append("nessun suono da scrivere")
        esito["completa"] = False
        return esito

    pezzi = _scansiona(ipa)
    if not pezzi:
        esito["dubbi"].append("nessun suono da scrivere")
        esito["completa"] = False
        return esito

    testo = ""
    # Il segno di accento sta davanti a una **sillaba**, e non sempre davanti
    # alla vocale: in `/fraˈrɛs/` e' sulla `r` e la vocale accentata arriva
    # dopo. Percio' l'accento viaggia in attesa, e viene usato dalla vocale
    # che segue. Senza questo, `/fraˈrɛs/` diventava `frares`, che rilegge
    # /e/ e non /ɛ/, e la parola cambiava suono tornando indietro.
    accento_in_attesa = False
    i = 0
    while i < len(pezzi):
        simbolo, tonica = pezzi[i]
        if tonica:
            accento_in_attesa = True

        # La `g` di IPA (U+0261, «script g») e la `g` comune sono lo stesso
        # suono scritti in due modi, e in un file di trascrizioni di
        # centottocento anni convivono senza problema. Non trattarle come due
        # suoni: significherebbe dichiarare non scrivibile meta' del file.
        if simbolo == "\u0261":
            simbolo = "g"

        if simbolo not in SIMBOLI_NOTI:
            esito["dubbi"].append(
                "suono %r: nessuna fonte dichiara come si scrive, quindi non "
                "si scrive a caso" % simbolo)
            esito["forma"] = testo
            esito["completa"] = False
            return esito

        if simbolo in AFFRICATE:
            # La lettera dipende dalla vocale che segue: e' la regola 4 letta
            # al contrario. La vocale viene scritta qui e poi **saltata**,
            # altrimenti si scrive due volte (`princii...` invece di `prin...`).
            seguente = pezzi[i + 1][0] if i + 1 < len(pezzi) else ""
            if seguente in VOCALI:
                # La vocale viene scritta **una volta sola**, con la sua
                # marcatura accentata decisa prima: prima si scriveva la
                # vocale nuda e poi, se era tonica, la si acccentava in
                # vocale in piu', e la parola si ripete: difetto preso
                # dalla misura, non dal codice.
                # piu' e due lettere che si parlavano sopra.
                if accento_in_attesa:
                    testo += AFFRICATE[simbolo] + _vocale(seguente, True)
                    accento_in_attesa = False
                else:
                    testo += AFFRICATE[simbolo] + _vocale(seguente, False)
                i += 2
            else:
                testo += AFFRICATE[simbolo]
                i += 1
            # Ogni percorso del ciclo avanza, o il ciclo non finisce: e' stato
            # un vero blocco in un'altra stesura, non un dettaglio.
            continue

        if simbolo == "\u0272" and i + 1 < len(pezzi) \
                and pezzi[i + 1][0] in CONSONANTI:
            # Il caso che nessuna regola risolve, e che va detto ad alta voce.
            # Il suono /\u0272/ scrive `gn`, ma solo davanti a vocale
            # anteriore: davanti a consonante la regola 3 non parla. La fonte
            # (Biondelli, `magnar` = /ma\u02c8\u0272nar/) scrive /\u0272/
            # seguito da /n/, che nessuna scrittura del progetto produce. Il
            # dubbio e' gia' nella nota di T0001: la consonante palatale
            # forse raddoppia, e la trascrizione sarebbe meta'. Qui non si
            # sceglie e non si inventa una `gnn` che nessuno ha scritta.
            esito["dubbi"].append(
                "/\u0272/ davanti a `%s`: si scriverebbe `gn`, ma la regola 3 "
                "parla solo di vocale anteriore e davanti a consonante tace. "
                "La fonte scrive /\u0272n/, che nessuna grafia del progetto "
                "produce: o la palatale e' raddoppiata, o manca una regola. "
                "Non si scrive a caso" % pezzi[i + 1][0])
            esito["forma"] = testo
            esito["completa"] = False
            return esito

        if simbolo == "g":
            # La `g` velare davanti a `e` o `i` si scrive `gh`, perche' la
            # regola 4 rende palatali la `g` e la `c` seguite da vocale
            # anteriore, e il modo per evitarlo e' proprio il digramma. Scrive
            # `ge` produrrebbe /dʒe/, che e' un altro suono. La regola 2 dice
            # `gh` = /g/ senza eccezioni, quindi qui si applica e basta.
            seguente = pezzi[i + 1][0] if i + 1 < len(pezzi) else ""
            if seguente in VOCALI and seguente not in "aou":
                testo += "gh"
                i += 1
                continue
            testo += CONSONANTI[simbolo]
            i += 1
            continue

        if simbolo in VOCALI or simbolo in VOCALI_TONICHE:
            testo += _vocale(simbolo, accento_in_attesa)
            accento_in_attesa = False
            i += 1
            continue

        if simbolo in S_E_Z:
            scelte = S_E_Z[simbolo]
            testo += scelte[0]
            esito["alternative"].append(scelte[1])
            esito["dubbi"].append(
                "/%s/ puo' scriversi `%s` o `%s`: la regola 6 dichiara che `s` "
                "e `z` si leggono come sono scritte e che non e' una regola, "
                "e nessuna fonte consultata sceglie"
                % ((simbolo,) + tuple(scelte)))
            i += 1
            continue

        testo += CONSONANTI[simbolo]
        i += 1

    esito["forma"] = testo
    esito["alternative"] = _alternative_uniche(testo, esito["alternative"])
    return esito


def _vocale(simbolo: str, tonica: bool) -> str:
    """La vocale con la sua marcatura accentata, se la porta.

    Due scelte di accento ci sono per ogni vocale tonica, e questo modulo non
    sa quale sia giusta: sceglie la prima, che e' la piu' comune
    nell'italiano dell'epoca, e la mette fra le alternative al posto del
    chiamante. Nessuna fonte dichiara la differenza, quindi dichiarare qui
    sarebbe inventare.
    """
    if not tonica:
        return VOCALI.get(simbolo, simbolo)
    scelte = VOCALI_TONICHE.get(simbolo)
    if not scelte:
        return VOCALI.get(simbolo, simbolo)
    return scelte[0]


def _alternative_uniche(testo: str, altre: list) -> list:
    """Le altre scritture, senza quelle uguali alla prima e senza ripetizioni."""
    uniche = []
    for altra in altre:
        if altra and altra not in uniche:
            uniche.append(altra)
    return uniche


def scelta_esplicita(ipa: str, scegliere_s: str = "") -> str:
    """La grafia, ma solo se qualcuno ha detto quale `s` scrivere.

    E' il punto in cui questo modulo serve un ascoltatore vero. Il dubbio su
    `s` e `z` non si risolve da solo, e risolverlo da solo e' quello che
    produrrebbe ferrarese inventato. Chi ha sentito la parola sa se quel suono
    e' una `s` o una `z`, e dicendolo qui si chiude il dubbio. Senza, la
    funzione non scrive niente e dice perche': un `None` e' piu' utile di una
    parola inventata.

    La sostituzione e' fatta in **un passaggio solo**, carattere per
    carattere. La prima stesura sostituiva prima `s` con `z` e poi `z` con
    `s`, e quindi la seconda passata annullava la prima: il risultato era una
    stringa vuota, cioe' il contrario di quello che era stata chiamata a fare.
    """
    esito = rinomina(ipa)
    if not scegliere_s:
        if esito["dubbi"]:
            return None
        return esito["forma"]
    if not esito["completa"]:
        return None

    # La scelta vale per il suono, quindi si applica a tutta la parola e
    # non solo alle lettere che erano gia' `s` o `z`: se chi ha ascoltato ha
    # detto `z`, vuol dire `z` ovunque.
    testo = esito["forma"]
    caratteri = list(testo)
    for pos, carattere in enumerate(caratteri):
        if carattere == "s":
            caratteri[pos] = scegliere_s
        elif carattere == "z":
            caratteri[pos] = "s" if scegliere_s == "z" else carattere
    return "".join(caratteri)
