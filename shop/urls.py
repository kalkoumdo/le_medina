from django.urls import path
from . import views

urlpatterns = [
    # Auth
    path('', views.login_view, name='login'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('inscription/', views.inscription_view, name='inscription'),

    # Pages principales
    path('accueil/', views.accueil_view, name='accueil'),
    path('plats/', views.plats_view, name='plats'),
    path('boissons/', views.boissons_view, name='boissons'),

    # Avis
    path('avis/', views.avis_view, name='avis'),
    path('avis/supprimer/', views.supprimer_avis, name='supprimer_avis'),

    # Panier
    path('panier/', views.panier_view, name='panier'),
    path('panier/ajouter/plat/<int:plat_id>/', views.ajouter_plat, name='ajouter_plat'),
    path('panier/ajouter/boisson/<int:boisson_id>/', views.ajouter_boisson, name='ajouter_boisson'),
    path('panier/supprimer/<int:item_id>/', views.supprimer_panier, name='supprimer_panier'),
    path('panier/vider/', views.vider_panier, name='vider_panier'),

    # Commandes
    path('commandes/', views.commandes_view, name='commandes'),
    path('commandes/valider/', views.valider_commande, name='valider_commande'),
    path('commandes/payer/<int:commande_id>/', views.payer_commande, name='payer_commande'),
    path('commandes/supprimer/<int:commande_id>/', views.supprimer_commande, name='supprimer_commande'),
    path('commandes/<int:commande_id>/', views.detail_commande, name='detail_commande'),

    # Compte
    path('compte/supprimer/', views.supprimer_compte, name='supprimer_compte'),

    # ── ADMIN CUSTOM ──
    path('panel/', views.admin_dashboard, name='admin_dashboard'),
    path('panel/commandes/', views.admin_commandes, name='admin_commandes'),
    path('panel/commandes/<int:commande_id>/statut/', views.admin_changer_statut, name='admin_changer_statut'),
    path('panel/commandes/<int:commande_id>/confirmer-paiement/', views.admin_confirmer_paiement, name='admin_confirmer_paiement'),
    path('panel/commandes/<int:commande_id>/supprimer/', views.admin_supprimer_commande, name='admin_supprimer_commande'),
    path('panel/plats/', views.admin_plats, name='admin_plats'),
    path('panel/plats/ajouter/', views.admin_ajouter_plat, name='admin_ajouter_plat'),
    path('panel/plats/<int:plat_id>/modifier/', views.admin_modifier_plat, name='admin_modifier_plat'),
    path('panel/plats/<int:plat_id>/supprimer/', views.admin_supprimer_plat, name='admin_supprimer_plat'),
    path('panel/boissons/', views.admin_boissons, name='admin_boissons'),
    path('panel/boissons/ajouter/', views.admin_ajouter_boisson, name='admin_ajouter_boisson'),
    path('panel/boissons/<int:boisson_id>/modifier/', views.admin_modifier_boisson, name='admin_modifier_boisson'),
    path('panel/boissons/<int:boisson_id>/supprimer/', views.admin_supprimer_boisson, name='admin_supprimer_boisson'),
    path('panel/avis/', views.admin_avis, name='admin_avis'),
    path('panel/avis/<int:avis_id>/supprimer/', views.admin_supprimer_avis, name='admin_supprimer_avis'),
    path('panel/utilisateurs/', views.admin_utilisateurs, name='admin_utilisateurs'),
    path('panel/utilisateurs/<int:user_id>/supprimer/', views.admin_supprimer_utilisateur, name='admin_supprimer_utilisateur'),
]