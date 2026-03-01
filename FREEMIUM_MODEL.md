# Modèle Freemium Phone Finder

## Vue d'ensemble

Phone Finder utilise un modèle freemium avec deux tiers :

### 📊 Tiers disponibles

| Fonctionnalité | Free | Premium |
|---|---|---|
| **Appareils max** | 25 | Illimité (999) |
| **Coût** | $0 | $4.99/mois |
| **Publicités** | Oui | Non |
| **Contrôle d'accès** | Oui | Oui |
| **Export (mBlock/micro:bit)** | Oui | Oui |
| **Audit log** | Administrateurs | Administrateurs |

---

## Architecture technique

### 1. **Module de facturation** (`billing.py`)

```python
from phone_finder import Tier, PricingPlan, FeatureLimitError

# Vérifier les limites
max_devices = PricingPlan.get_limit(Tier.FREE)  # 25

# Afficher le tarif
price = PricingPlan.get_price(Tier.PREMIUM)  # $4.99
```

### 2. **Modèle utilisateur enrichi** (`models.py`)

```python
@dataclass(frozen=True)
class User:
    username: str
    role: Role
    tier: Tier = Tier.FREE              # Nouveau
    subscription_id: str | None = None  # Nouveau
    device_count: int = 0               # Nouveau
```

### 3. **Base de données** (`db.py`)

Nouvelles colonnes :
```sql
CREATE TABLE users (
    username TEXT PRIMARY KEY,
    role TEXT NOT NULL,
    tier TEXT DEFAULT 'free',        -- free | premium
    subscription_id TEXT,             -- ID PayPal
    device_count INTEGER DEFAULT 0,   -- Suivi
    created_at TIMESTAMP,
    last_payment_date TIMESTAMP
);
```

### 4. **Service avec limites** (`service.py`)

```python
def detect_phones(self, actor: User, connected_devices: list[dict]) -> list[Phone]:
    # ...
    max_devices = PricingPlan.get_limit(actor.tier)
    if len(phones) > max_devices:
        raise FeatureLimitError(max_devices, len(phones), actor.tier)
```

---

## Flux utilisateur

### Scénario 1 : Utilisateur Free atteint la limite

```python
prof = service.resolve_user("prof")  # Tier: FREE

# Essayer de détecter 26 appareils
try:
    phones = service.detect_phones(prof, devices_26)
except FeatureLimitError as e:
    # "Limite de 25 appareils atteinte..."
    
    # Option 1: Regarder une publicité
    new_count = service.watch_ad_for_bonus(prof)  # +5 devices
    
    # Option 2: Upgrader vers Premium
    service.upgrade_to_premium(prof, subscription_id="I-ABC123")
```

### Scénario 2 : Upgrade PayPal

```python
# 1. Créer une souscription PayPal
sub_response = PayPalHelper.create_subscription(
    user_email="user@example.com",
    plan_id="PREMIUM_MONTHLY"
)
# Retour: {"subscription_id": "I-ABC123", "approval_url": "..."}

# 2. Utilisateur approuve sur PayPal

# 3. Vérifier et upgrader
if PayPalHelper.verify_subscription(sub_response["subscription_id"]):
    service.upgrade_to_premium(prof, sub_response["subscription_id"])
    # prof.tier = Tier.PREMIUM
```

---

## Implémentation PayPal

### Configuration requise

```python
# À ajouter en production
PAYPAL_CLIENT_ID = "..."
PAYPAL_CLIENT_SECRET = "..."
PAYPAL_PLAN_ID = "..."
```

### Exemple d'intégration

```python
from phone_finder import PayPalHelper

# Créer une souscription
subscription = PayPalHelper.create_subscription(
    user_email="student@school.edu",
    plan_id="PREMIUM_MONTHLY",
    sandbox=False  # True pour les tests
)

# Vérifier l'état
is_active = PayPalHelper.verify_subscription(subscription["subscription_id"])

# Annuler
PayPalHelper.cancel_subscription(subscription["subscription_id"])
```

---

## Publicités & Récompenses

### Placement publicitaire

```python
from phone_finder import AdPlacement

ad = AdPlacement.get_free_tier_ad()
# {
#     "ad_type": "interstitial",
#     "message": "Limite de 25 appareils...",
#     "action_url": "https://phone-finder.example.com/upgrade",
#     "reward_description": "Ajouter 5 appareils temporaires"
# }
```

### Mécanique d'engagement

1. **Utilisateur Free** détecte 25 appareils → Limite atteinte
2. **Affiche publicité** → Option : regarder pub ou upgrader
3. **Regarde pub** → Reçoit 5 devices supplémentaires
4. **Peut continuer** → Jusqu'à 30 devices, puis pub à nouveau

---

## Tests

### Vérifier les limites

```bash
# Tests unitaires fournis :
python -m unittest test_service.PhoneFinderServiceTests.test_free_tier_has_25_device_limit
python -m unittest test_service.PhoneFinderServiceTests.test_premium_tier_unlimited_devices
python -m unittest test_service.PhoneFinderServiceTests.test_pricing_plan_free_tier
```

### Demo complète

```bash
PYTHONPATH=src python main.py
```

---

## Roadmap future

- [ ] Dashboard utilisateur (web)
- [ ] Analytics : nombre de detections par tier
- [ ] Limite mensuelle d'API calls pour Premium
- [ ] Intégration Stripe comme alternative
- [ ] Webhooks PayPal pour événements
- [ ] Batch emails pour expired subscriptions

---

## Questions fréquentes

**Q: Peut-on downgrade de Premium vers Free ?**
A: Le code ne supporte pas le downgrade actuellement. À implémenter selon vos règles commerciales.

**Q: Que se passe-t-il si la souscription PayPal expire ?**
A: Actuellement pas de gestion automatique. À ajouter avec webhooks PayPal.

**Q: Maximum d'appareils pour Premium ?**
A: 999 (configurable dans `PricingPlan.PLANS`)

**Q: Les données de paiement sont-elles stockées ?**
A: Non, juste l'ID souscription PayPal pour vérification.

---

## Support

Pour questions sur le modèle financier ou l'implémentation PayPal, consulter :
- PayPal REST API docs
- `src/phone_finder/billing.py`
