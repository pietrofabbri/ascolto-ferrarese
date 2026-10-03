# AGENTS.md — ascolto-ferrarese

Repository fratello di `traduttore-ferrarese`. Le regole del progetto valgono
qui uguali, e in questo foglio sono ripetute solo quelle che **qui** mordono di
piu'. Dove il progetto dice «vedi `traduttore-ferrarese/AGENTS.md`», quel
documento e' la regola e questo non la sostituisce.

## Le regole che non si spostano

1. **Nessuna risposta senza fonte.** Una scrittura ferrarese proposta qui porta
   la fonte da cui viene, o la dichiarazione che non ce l'ha.
2. **Nessun vuoto riempito a caso.** Se non si sa, si dice che non si sa. Vale
   anche — e soprattutto — per i suoni: una vocale acustica che il modello
   sbaglia non diventa una lettera a caso.
3. **I controlli segnalano, non correggono.**
4. **Nessun dato di studente**, nessun account, nessuna telemetria.
5. **Codice MIT**, dati con licenza dichiarata per voce. Una fonte con licenza
   non verificata non entra nei dati attivi.
6. **Nessuna rete a runtime.** Qui vale più che altrove: un sistema che
   ascolta e manda audio fuori da casa è un sistema che registra persone senza
   che nessuno lo sappia.

## La regola che questo repository aggiunge

**Un sistema che ascolta il ferrarese deve poter dire che non ha capito.**

Non è una buona pratica, è la condizione che rende il progetto onesto. Il
ferrarese è una lingua che ha perso metà del suo lessico: chi la parla oggi la
sa per contesto, non per dizionario. Un sistema che completa le frasi senza
dovere produce **ferrarese inventato**, cioè l'illusione più dannosa che si
possa fare a un dialetto — perché sembra che la lingua ci sia ancora, e invece
si è fabbricata roba nuova.

Quindi:

- ogni risultato porta `attendibilita` e l'elenco dei dubbi;
- l'astensione è un esito **previsto**, non un errore da gestire;
- nessuna soglia di confidenza viene scelta per far sembrare il sistema più
  bravo di quanto sia. Una soglia si dichiara e si motiva.

## Sul modello acustico

Il modello che non conosce il ferrarese va detto tale e quale, ogni volta che
appare. Non è un dettaglio da mettere in una nota a piè di pagina: è la
ragione per cui esiste il vincolo di lessico.

E vale la regola che nel traduttore è già scritta per i dati: **un modello
fine-tuned su poche ore di una lingua minoritaria rischia di essere peggio di
un modello generico vincolato**, perché ha visto troppo poco per generalizzare
e ha imparato il modo di parlare di chi ha registrato per primo. Se un giorno si
prova, si confronta col generico e si pubblica il confronto, anche se il
fine-tuned perde.

## Sul vincolo di lessico

Il passo che trasforma un suono in una parola ferrarese è l'unico che conosce
il dialetto, ed è nostro. Le sue regole sono **le stesse** del traduttore e
sono tenute allimate a mano, in due copie. Il fatto che siano due copie è un
costo noto e dichiarato: `prove/roundtrip.py` confronta i risultati e il numero
dice se vanno ancora d'accordo. Se il numero scende, è un difetto, e si cerca.

## Prima di aggiungere una dipendenza

Il progetto non ha dipendenze e può restare così finché possibile. Un modello
acustico sarà inevitabilmente una dipendenza pesante, e va tenuta **fuori**
dal percorso di default: il default deve restare eseguibile senza rete e senza
modelli, perché è quello che gira in un'aula con il computer spento.

## Quando una misura cambia numero

Un numero che cambia senza che nessuno sappia perché è un numero che non vale
niente. Se `roundtrip` passa dal 96% a qualcos'altro, nel messaggio del commit
c'è la ragione. Se non c'è, il numero è sceso per caso e va raddoppiato per
capire cosa è successo.