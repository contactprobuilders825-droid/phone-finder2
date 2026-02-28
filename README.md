# phone-finder2

Prototype de logiciel de détection de téléphones avec export automatique d'un programme adapté :

- robot **mBlock**,
- carte **micro:bit**.

Le système intègre 3 rôles persistés en **base SQL (SQLite)** :

- `utilisateur` (profs) : détection + téléchargement de programme,
- `admin` (direction) : idem + accès audit,
- `super_admin` (owner) : tous les droits.

## Architecture (v2)

- `src/phone_finder/db.py` : gestion SQL (`users`) et bootstrap des rôles.
- `src/phone_finder/service.py` : logique métier + contrôle d'accès.
- `src/phone_finder/adapters.py` : génération du programme mBlock / micro:bit.

## Lancer la démo

```bash
PYTHONPATH=src python main.py
```

## Lancer les tests

```bash
PYTHONPATH=src python -m unittest discover -s tests
```
