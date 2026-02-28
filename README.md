# phone-finder2

Prototype de logiciel de détection de téléphones avec export automatique d'un programme adapté :

- robot **mBlock**,
- carte **micro:bit**.

Le système intègre 3 rôles persistés en **base SQL (SQLite)** :

- `utilisateur` (profs) : détection + téléchargement de programme,
- `admin` (direction) : idem + accès audit,
- `super_admin` (owner) : tous les droits.

## Dépendances matériel

Le projet utilise les bibliothèques demandées :

- `uflash` pour flasher les cartes micro:bit,
- `pymata-express` pour piloter/sonder les robots compatibles,
- `pyserial` pour envoyer un programme sur port série (mBlock).

## Installation client + compilation automatique

Le fichier `INSTALL_CLIENT.txt` contient une commande unique pour :

1. installer les dépendances,
2. compiler automatiquement le code Python sur le poste client.

## Architecture (v3)

- `src/phone_finder/db.py` : gestion SQL (`users`) et bootstrap des rôles.
- `src/phone_finder/service.py` : logique métier + contrôle d'accès + déploiement matériel.
- `src/phone_finder/deployment.py` : intégration `uflash`, `pymata-express`, `pyserial`.
- `src/phone_finder/adapters.py` : génération du programme mBlock / micro:bit.

## Lancer la démo

```bash
PYTHONPATH=src python main.py
```

## Lancer les tests

```bash
PYTHONPATH=src python -m unittest discover -s tests
```
