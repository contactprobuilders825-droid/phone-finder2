"""Système de facturation, limites de devices, et gestion des publicités."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Tier(str, Enum):
    """Niveaux d'abonnement disponibles."""

    FREE = "free"
    PREMIUM = "premium"


class PricingPlan:
    """Limites et tarifs par tier."""

    PLANS = {
        Tier.FREE: {
            "max_devices": 25,
            "monthly_price": 0.0,
            "currency": "USD",
            "show_ads": True,
            "description": "Free with ads - 25 devices",
        },
        Tier.PREMIUM: {
            "max_devices": 999,  # Pratiquement illimité
            "monthly_price": 4.99,
            "currency": "USD",
            "show_ads": False,
            "description": "Premium - Unlimited devices, no ads",
        },
    }

    @classmethod
    def get_limit(cls, tier: Tier) -> int:
        """Retourne le nombre max de devices pour un tier."""
        return cls.PLANS[tier]["max_devices"]

    @classmethod
    def needs_ads(cls, tier: Tier) -> bool:
        """Retourne si le tier doit afficher des publicités."""
        return cls.PLANS[tier]["show_ads"]

    @classmethod
    def get_price(cls, tier: Tier) -> float:
        """Retourne le prix mensuel pour un tier."""
        return cls.PLANS[tier]["monthly_price"]


class FeatureLimitError(Exception):
    """Levé quand l'utilisateur a dépassé sa limite de devices."""

    def __init__(self, max_devices: int, current_count: int, tier: Tier):
        self.max_devices = max_devices
        self.current_count = current_count
        self.tier = tier
        super().__init__(
            f"Limite de {max_devices} appareils atteinte (vous en avez {current_count}). "
            f"Passez à Premium pour des appareils illimités, ou regardez une publicité."
        )


@dataclass
class AdPlacement:
    """Placement publicitaire pour les utilisateurs Free."""

    ad_type: str  # "banner", "interstitial", "reward_video"
    message: str
    action_url: str
    reward_description: str = "Ajouter 5 appareils temporaires"

    @staticmethod
    def get_free_tier_ad() -> AdPlacement:
        """Publicité standard pour les utilisateurs Free."""
        return AdPlacement(
            ad_type="interstitial",
            message="Vous avez atteint la limite de 25 appareils gratuits!\n"
            "Regardez une courte publicité ou passez à Premium.",
            action_url="https://phone-finder.example.com/upgrade",
            reward_description="Ajouter 5 appareils détectés",
        )


class PayPalHelper:
    """Intégration avec PayPal pour les paiements."""

    BASE_URL = "https://api.paypal.com"
    SANDBOX_URL = "https://api.sandbox.paypal.com"

    @staticmethod
    def create_subscription(
        user_email: str,
        plan_id: str = "PREMIUM_MONTHLY",
        sandbox: bool = False,
    ) -> dict:
        """
        Crée une souscription PayPal.

        Args:
            user_email: Email de l'utilisateur
            plan_id: ID du plan (ex: PREMIUM_MONTHLY)
            sandbox: Utiliser le sandbox PayPal pour les tests

        Returns:
            Dict avec subscription_id et approval_url
        """
        # Implémentation simplifiée - à adapter avec la vraie API
        return {
            "subscription_id": f"I-{user_email.split('@')[0][:8].upper()}",
            "approval_url": f"https://www.paypal.com/subscribe?user={user_email}",
            "status": "PENDING_APPROVAL",
        }

    @staticmethod
    def verify_subscription(subscription_id: str, sandbox: bool = False) -> bool:
        """Vérifie qu'une souscription PayPal est active."""
        # À implémenter avec l'API PayPal réelle
        return bool(subscription_id)

    @staticmethod
    def cancel_subscription(subscription_id: str, sandbox: bool = False) -> bool:
        """Annule une souscription PayPal."""
        # À implémenter avec l'API PayPal réelle
        return bool(subscription_id)


class BillingManager:
    """Gère les limites d'usage, les pubs, et les paiements."""

    def __init__(self, user_tier: Tier = Tier.FREE, device_count: int = 0):
        self.user_tier = user_tier
        self.device_count = device_count

    def can_add_device(self) -> tuple[bool, AdPlacement | None]:
        """
        Vérifie si l'utilisateur peut ajouter un apareil.

        Returns:
            (peut_ajouter, publicite_si_besoin)
        """
        max_devices = PricingPlan.get_limit(self.user_tier)

        if self.device_count < max_devices:
            return True, None

        if self.user_tier == Tier.FREE:
            return False, AdPlacement.get_free_tier_ad()

        # Tier Premium sans limite
        return True, None

    def upgrade_to_premium(self, subscription_id: str) -> bool:
        """Upgrade l'utilisateur vers Premium via PayPal."""
        if PayPalHelper.verify_subscription(subscription_id):
            self.user_tier = Tier.PREMIUM
            return True
        return False

    def watch_ad(self) -> int:
        """Utilisateur regarde une pub, obtient des devices temporaires."""
        ad_bonus = 5
        self.device_count = min(
            self.device_count + ad_bonus,
            PricingPlan.get_limit(self.user_tier),
        )
        return ad_bonus
