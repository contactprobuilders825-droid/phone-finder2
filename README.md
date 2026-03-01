# phone-finder2

Logiciel de détection de téléphones avec export automatique d'un programme adapté :

- robot **mBlock**,
- carte **micro:bit**.

**Modèle freemium avec système de facturation PayPal intégré.**

## 🎯 Caractéristiques

### Détection et Export
- Détection automatique de téléphones connectés
- Export vers robot mBlock ou carte micro:bit
- Génération de code adapté au matériel cible

### Système de Rôles (RBAC)
Le système intègre 3 rôles persistés en **base SQL (SQLite)** :

| Rôle | Tier | Capacités |
|------|------|----------|
| `utilisateur` (prof) | Free/Premium | Détection + téléchargement |
| `admin` (direction) | Premium | + audit log, gestion utilisateurs |
| `super_admin` (owner) | Premium | Tous les droits |

### Modèle Freemium
| Tier | Devices max | Prix | Publicités | PayPal |
|------|-------------|------|-----------|--------|
| **FREE** | 25 | $0 | Oui | Non |
| **PREMIUM** | 999 | $4.99/mois | Non | Oui |

**Fonctionnalités:**
- ✅ Limite de 25 appareils pour Free
- ✅ Publicités interstitielles pour les Free
- ✅ Upgrade Premium via PayPal
- ✅ Bonus +5 devices après visualisation d'une pub
- ✅ Stockage du statut d'abonnement en base de données

## Dépendances matériel

Le projet utilise les bibliothèques demandées :

- `uflash` pour flasher les cartes micro:bit,
- `pymata-express` pour piloter/sonder les robots compatibles,
- `pyserial` pour envoyer un programme sur port série (mBlock).

## Installation client + compilation automatique

Le fichier `INSTALL_CLIENT.txt` contient une commande unique pour :

1. installer les dépendances,
2. compiler automatiquement le code Python sur le poste client.

```bash
python -m pip install --upgrade pip && \
python -m pip install -r requirements.txt && \
python -m compileall src main.py
```

## Architecture (v4)

### Core Modules
- `src/phone_finder/db.py` : gestion SQL (users avec tier/subscription) et bootstrap.
- `src/phone_finder/service.py` : logique métier, contrôle d'accès, déploiement.
- `src/phone_finder/rbac.py` : contrôle d'accès basé rôles.
- `src/phone_finder/models.py` : dataclasses (User, Phone, Role, Tier).

### Facturation & Hardware
- `src/phone_finder/billing.py` : **NOUVEAU** - Tiers, pricing, pubs, PayPal.
- `src/phone_finder/deployment.py` : intégration uflash, pymata-express, pyserial.
- `src/phone_finder/adapters.py` : génération code mBlock / micro:bit.

### Schéma Base de Données
```sql
users (
  username TEXT PRIMARY KEY,
  role TEXT,
  tier TEXT DEFAULT 'free' CHECK (tier IN ('free', 'premium')),
  subscription_id TEXT,
  device_count INTEGER DEFAULT 0,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  last_payment_date TIMESTAMP
)
```

## Lancer la démo

```bash
PYTHONPATH=src python main.py
```

Cela affichera :
1. Test utilisateur Free (limite 25 devices)
2. Détection avec limite respectée
3. Utilisateur Premium (illimité)
4. Plans de pricing
5. Logs d'audit

## Lancer les tests

```bash
PYTHONPATH=src python -m unittest discover -s tests
```

**Résultat:** 22/22 tests passent ✅

### Tests inclus
- Détection et filtrage de phones
- Vérification des limites par tier
- Permissions RBAC
- Système de pricing
- Publicités et bonus ad
- Upgrade vers Premium
- Persistance en base de données

## API Usage

### Créer un service
```python
from phone_finder import make_sql_service, connect

conn = connect("phone_finder.db")
service = make_sql_service(conn)
```

### Détecter des téléphones
```python
prof = service.resolve_user("prof")  # Tier Free
phones = service.detect_phones(prof, [
    {"kind": "phone", "serial_number": "A1", "is_powered_on": True},
    {"kind": "phone", "serial_number": "B2", "is_powered_on": False},
])
```

### Exporter un programme
```python
from phone_finder.models import DeviceTarget

program = service.download_adapter(prof, DeviceTarget.MICROBIT, phones)
print(program)  # MicroPython code
```

### Upgrade vers Premium
```python
from phone_finder.billing import PayPalHelper

sub = PayPalHelper.create_subscription(prof.username + "@example.com")
service.upgrade_to_premium(prof, sub["subscription_id"])
```

### Regarder une pub pour bonus
```python
new_device_count = service.watch_ad_for_bonus(prof)
```

## Support matériel

### mBlock
- Export du code mBlock prêt à copier-coller
- Compatible avec robots Makeblock
- Envoi via `pyserial` sur port série

### micro:bit
- Export du code MicroPython
- Flashage automatique avec `uflash`
- Détection automatique du port

## Gestion des erreurs

```python
from phone_finder.billing import FeatureLimitError

try:
    phones = service.detect_phones(prof, devices_26)
except FeatureLimitError as e:
    print(e.message)  
    # "Limite de 25 appareils... Passez à Premium ou regardez une pub"
```

## Logs d'audit

```python
admin = service.resolve_user("direction")  # Admin
logs = service.get_audit_log(admin)

for log in logs:
    print(log)
    # "prof a lancé une détection: 2 téléphone(s)."
    # "prof a généré un adaptateur mblock (2 téléphone(s))."
```

## Compilation

```bash
python -m compileall src main.py
```

Génère les fichiers `.pyc` pour optimiser le démarrage.

## Développement

```bash
# Cloner le repo
git clone https://github.com/contactprobuilders825-droid/phone-finder2.git
cd phone-finder2

# Installer les deps
pip install -r requirements.txt

# Lancer la démo
PYTHONPATH=src python main.py

# Lancer les tests
PYTHONPATH=src python -m unittest discover -s tests -v
```

## Prochaines étapes

- [ ] Interface web (Flask/FastAPI)
- [ ] Dashboard utilisateur
- [ ] Analytiques PayPal
- [ ] Support multi-langue
- [ ] API REST pour les apps tierces
- [ ] Webhooks PayPal pour synchronisation
