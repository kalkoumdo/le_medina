from django.contrib import admin
from .models import Plat, Boisson, Panier, Commande, LigneCommande, Commentaire, Categorie

admin.site.register(Plat)
admin.site.register(Boisson)
admin.site.register(Panier)
admin.site.register(Commande)
admin.site.register(LigneCommande)
admin.site.register(Commentaire)
admin.site.register(Categorie)