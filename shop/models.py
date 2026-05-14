from django.db import models
from django.contrib.auth.models import User

PAYS = [
    ('BF', 'Burkina Faso'),
    ('TG', 'Togo'),
    ('CI', "Côte d'Ivoire"),
    ('ML', 'Mali'),
    ('BJ', 'Bénin'),
]

class Categorie(models.Model):
    nom = models.CharField(max_length=100)

    def __str__(self):
        return self.nom


class Plat(models.Model):
    CATEGORIES = [
        ('plat', 'Plat principal'),
        ('accompagnement', 'Accompagnement'),
        ('dessert', 'Dessert'),
    ]
    nom = models.CharField(max_length=100)
    prix = models.DecimalField(max_digits=8, decimal_places=2)
    disponible = models.BooleanField(default=True)
    categorie = models.CharField(max_length=20, choices=CATEGORIES, blank=True)
    pays = models.CharField(max_length=2, choices=PAYS, blank=True)
    image = models.ImageField(upload_to='plats/', null=True, blank=True)

    def __str__(self):
        return self.nom


class Boisson(models.Model):
    CATEGORIES = [
        ('naturelle', 'Boisson naturelle'),
        ('traditionnelle', 'Boisson traditionnelle'),
        ('alcoolisee', 'Boisson alcoolisée'),
    ]
    nom = models.CharField(max_length=100)
    prix = models.DecimalField(max_digits=8, decimal_places=2)
    disponible = models.BooleanField(default=True)
    categorie = models.CharField(max_length=20, choices=CATEGORIES, blank=True)
    pays = models.CharField(max_length=2, choices=PAYS, blank=True)
    image = models.ImageField(upload_to='boissons/', null=True, blank=True)

    def __str__(self):
        return self.nom


class Commande(models.Model):
    MODE_CHOICES = [
        ('retrait', 'Retrait sur place'),
        ('livraison', 'Livraison à domicile'),
    ]
    STATUT_CHOICES = [
        ('en_attente', 'En attente'),
        ('en_preparation', 'En préparation'),
        ('livree', 'Livrée'),
        ('annulee', 'Annulée'),
    ]
    utilisateur = models.ForeignKey(User, on_delete=models.CASCADE)
    date_commande = models.DateTimeField(auto_now_add=True)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    paye = models.BooleanField(default=False)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='en_attente')
    mode_recuperation = models.CharField(max_length=20, choices=MODE_CHOICES, default='retrait')

    # ── LOCALISATION ──
    adresse_livraison = models.CharField(max_length=500, blank=True, default='')
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    def __str__(self):
        return f"Commande #{self.id} - {self.utilisateur.username}"


class LigneCommande(models.Model):
    commande = models.ForeignKey(Commande, on_delete=models.CASCADE, related_name='lignes')
    plat = models.ForeignKey(Plat, on_delete=models.SET_NULL, null=True, blank=True)
    boisson = models.ForeignKey(Boisson, on_delete=models.SET_NULL, null=True, blank=True)
    quantite = models.IntegerField(default=1)
    prix_unitaire = models.DecimalField(max_digits=8, decimal_places=2)

    def sous_total(self):
        return self.quantite * self.prix_unitaire

    @property
    def nom_article(self):
        if self.plat:
            return self.plat.nom
        if self.boisson:
            return self.boisson.nom
        return '—'


class Panier(models.Model):
    utilisateur = models.ForeignKey(User, on_delete=models.CASCADE)
    plat = models.ForeignKey(Plat, on_delete=models.CASCADE, null=True, blank=True)
    boisson = models.ForeignKey(Boisson, on_delete=models.CASCADE, null=True, blank=True)
    quantite = models.IntegerField(default=1)

    def prix_unitaire(self):
        if self.plat:
            return self.plat.prix
        if self.boisson:
            return self.boisson.prix
        return 0

    def sous_total(self):
        return self.quantite * self.prix_unitaire()

    @property
    def nom_article(self):
        if self.plat:
            return self.plat.nom
        if self.boisson:
            return self.boisson.nom
        return '—'

    def __str__(self):
        produit = self.plat or self.boisson
        return f"{self.utilisateur.username} - {produit} x{self.quantite}"


class Commentaire(models.Model):
    NOTE_CHOICES = [(i, f"{i} étoile{'s' if i > 1 else ''}") for i in range(1, 6)]

    utilisateur = models.ForeignKey(User, on_delete=models.CASCADE)
    contenu = models.TextField()
    note = models.IntegerField(choices=NOTE_CHOICES, default=5)
    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"Avis de {self.utilisateur.username} ({self.note}★)"