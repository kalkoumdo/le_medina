from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from .models import Plat, Boisson, Panier, Commande, LigneCommande, Categorie, Commentaire


def staff_required(view_func):
    return user_passes_test(lambda u: u.is_staff, login_url='accueil')(view_func)


# ─── AUTH ────────────────────────────────────────────────────────────────────

def login_view(request):
    if request.user.is_authenticated:
        return redirect('accueil')
    form = AuthenticationForm()
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('accueil')
        else:
            messages.error(request, "Identifiants incorrects.")
    return render(request, 'shop/login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('login')


def inscription_view(request):
    if request.user.is_authenticated:
        return redirect('accueil')
    form = UserCreationForm()
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Bienvenue, {user.username} !")
            return redirect('accueil')
    return render(request, 'shop/inscription.html', {'form': form})


# ─── PAGES PRINCIPALES ───────────────────────────────────────────────────────

@login_required
def accueil_view(request):
    plats_vedette = Plat.objects.filter(disponible=True)[:3]
    boissons_vedette = Boisson.objects.filter(disponible=True)[:3]
    nb_panier = Panier.objects.filter(utilisateur=request.user).count()
    derniers_avis = Commentaire.objects.select_related('utilisateur').all()[:3]
    return render(request, 'shop/accueil.html', {
        'plats_vedette': plats_vedette,
        'boissons_vedette': boissons_vedette,
        'nb_panier': nb_panier,
        'derniers_avis': derniers_avis,
    })


@login_required
def plats_view(request):
    categories = Plat.CATEGORIES
    cat_filtre = request.GET.get('categorie')
    plats = Plat.objects.filter(disponible=True)
    if cat_filtre:
        plats = plats.filter(categorie=cat_filtre)
    nb_panier = Panier.objects.filter(utilisateur=request.user).count()
    return render(request, 'shop/plats.html', {
        'plats': plats, 'categories': categories,
        'cat_id': cat_filtre, 'nb_panier': nb_panier,
    })


@login_required
def boissons_view(request):
    categories = Boisson.CATEGORIES
    cat_filtre = request.GET.get('categorie')
    boissons = Boisson.objects.filter(disponible=True)
    if cat_filtre:
        boissons = boissons.filter(categorie=cat_filtre)
    nb_panier = Panier.objects.filter(utilisateur=request.user).count()
    return render(request, 'shop/boissons.html', {
        'boissons': boissons, 'categories': categories,
        'cat_id': cat_filtre, 'nb_panier': nb_panier,
    })


# ─── AVIS ────────────────────────────────────────────────────────────────────

@login_required
def avis_view(request):
    nb_panier = Panier.objects.filter(utilisateur=request.user).count()
    avis = Commentaire.objects.select_related('utilisateur').all()
    mon_avis = Commentaire.objects.filter(utilisateur=request.user).first()
    if request.method == 'POST':
        contenu = request.POST.get('contenu', '').strip()
        note = request.POST.get('note', '5')
        if not contenu:
            messages.error(request, "Le commentaire ne peut pas être vide.")
            return redirect('avis')
        try:
            note = int(note)
            if note < 1 or note > 5:
                note = 5
        except ValueError:
            note = 5
        if mon_avis:
            mon_avis.contenu = contenu
            mon_avis.note = note
            mon_avis.save()
            messages.success(request, "Votre avis a été mis à jour.")
        else:
            Commentaire.objects.create(utilisateur=request.user, contenu=contenu, note=note)
            messages.success(request, "Merci pour votre avis !")
        return redirect('avis')
    return render(request, 'shop/avis.html', {
        'avis': avis, 'mon_avis': mon_avis, 'nb_panier': nb_panier,
    })


@login_required
def supprimer_avis(request):
    avis = Commentaire.objects.filter(utilisateur=request.user).first()
    if avis:
        avis.delete()
        messages.success(request, "Votre avis a été supprimé.")
    return redirect('avis')


# ─── PANIER ──────────────────────────────────────────────────────────────────

@login_required
def panier_view(request):
    items = Panier.objects.filter(utilisateur=request.user)
    total = sum(item.sous_total() for item in items)
    return render(request, 'shop/panier.html', {
        'items': items, 'total': total,
        'total_int': int(total), 'nb_panier': items.count(),
    })


@login_required
def ajouter_plat(request, plat_id):
    plat = get_object_or_404(Plat, id=plat_id, disponible=True)
    item, created = Panier.objects.get_or_create(
        utilisateur=request.user, plat=plat, boisson=None, defaults={'quantite': 1}
    )
    if not created:
        item.quantite += 1
        item.save()
    messages.success(request, f"« {plat.nom} » ajouté au panier.")
    return redirect(request.META.get('HTTP_REFERER', 'plats'))


@login_required
def ajouter_boisson(request, boisson_id):
    boisson = get_object_or_404(Boisson, id=boisson_id, disponible=True)
    item, created = Panier.objects.get_or_create(
        utilisateur=request.user, boisson=boisson, plat=None, defaults={'quantite': 1}
    )
    if not created:
        item.quantite += 1
        item.save()
    messages.success(request, f"« {boisson.nom} » ajouté au panier.")
    return redirect(request.META.get('HTTP_REFERER', 'boissons'))


@login_required
def supprimer_panier(request, item_id):
    item = get_object_or_404(Panier, id=item_id, utilisateur=request.user)
    item.delete()
    messages.success(request, "Article retiré du panier.")
    return redirect('panier')


@login_required
def vider_panier(request):
    Panier.objects.filter(utilisateur=request.user).delete()
    messages.success(request, "Panier vidé.")
    return redirect('panier')


# ─── COMMANDES ───────────────────────────────────────────────────────────────

@login_required
def commandes_view(request):
    if request.user.is_staff:
        commandes = Commande.objects.all().order_by('-date_commande')
    else:
        commandes = Commande.objects.filter(utilisateur=request.user).order_by('-date_commande')
    nb_panier = Panier.objects.filter(utilisateur=request.user).count()
    maintenant = timezone.now()
    for cmd in commandes:
        cmd.annulable = (maintenant - cmd.date_commande) < timedelta(minutes=15)
    return render(request, 'shop/commandes.html', {
        'commandes': commandes, 'nb_panier': nb_panier,
    })


@login_required
def valider_commande(request):
    items = Panier.objects.filter(utilisateur=request.user)
    if not items.exists():
        messages.error(request, "Votre panier est vide.")
        return redirect('panier')
    mode = request.POST.get('mode_recuperation', 'retrait')
    adresse = request.POST.get('adresse_livraison', '').strip()
    lat = request.POST.get('latitude', '').strip()
    lng = request.POST.get('longitude', '').strip()
    if mode == 'livraison' and not adresse:
        messages.error(request, "Veuillez indiquer une adresse de livraison.")
        return redirect('panier')
    sous_total = sum(item.sous_total() for item in items)
    frais_livraison = 750 if mode == 'livraison' else 0
    total = sous_total + frais_livraison
    commande = Commande.objects.create(
        utilisateur=request.user, total=total, mode_recuperation=mode,
        adresse_livraison=adresse,
        latitude=float(lat) if lat else None,
        longitude=float(lng) if lng else None,
    )
    for item in items:
        LigneCommande.objects.create(
            commande=commande, plat=item.plat, boisson=item.boisson,
            quantite=item.quantite, prix_unitaire=item.prix_unitaire(),
        )
    items.delete()
    messages.success(request, f"Commande #{commande.pk} créée avec succès !")
    return redirect('detail_commande', commande_id=commande.pk)


@login_required
def detail_commande(request, commande_id):
    if request.user.is_staff:
        commande = get_object_or_404(Commande, id=commande_id)
    else:
        commande = get_object_or_404(Commande, id=commande_id, utilisateur=request.user)
    nb_panier = Panier.objects.filter(utilisateur=request.user).count()
    maintenant = timezone.now()
    annulable = (maintenant - commande.date_commande) < timedelta(minutes=15)
    secondes_restantes = max(0, int(
        (commande.date_commande + timedelta(minutes=15) - maintenant).total_seconds()
    ))
    return render(request, 'shop/detail_commande.html', {
        'commande': commande, 'nb_panier': nb_panier,
        'annulable': annulable, 'secondes_restantes': secondes_restantes,
    })


@login_required
def payer_commande(request, commande_id):
    commande = get_object_or_404(Commande, id=commande_id, utilisateur=request.user)
    if not commande.paye:
        methode = request.POST.get('methode', '')
        operateur = request.POST.get('operateur', '')
        telephone = request.POST.get('telephone', '')

        if methode == 'especes':
            # Espèces : commande confirmée mais pas encore payée
            # L'admin devra confirmer manuellement la réception
            commande.statut = 'en_attente'
            commande.save()
            messages.success(request,
                f"✅ Commande confirmée. Paiement en espèces à effectuer "
                f"{'à la livraison' if commande.mode_recuperation == 'livraison' else 'sur place'}."
            )
        else:
            # Mobile Money : paiement immédiatement confirmé
            commande.paye = True
            commande.statut = 'en_preparation'
            commande.save()
            if operateur and telephone:
                messages.success(request,
                    f"✅ Paiement {operateur} de {commande.total:,.0f} FCFA confirmé depuis le {telephone} !")
            else:
                messages.success(request,
                    f"✅ Paiement de {commande.total:,.0f} FCFA confirmé !")

    return redirect('detail_commande', commande_id=commande.pk)


@login_required
def supprimer_commande(request, commande_id):
    commande = get_object_or_404(Commande, id=commande_id, utilisateur=request.user)
    if (timezone.now() - commande.date_commande) >= timedelta(minutes=15):
        messages.error(request, "Cette commande ne peut plus être annulée (délai de 15 min dépassé).")
        return redirect('detail_commande', commande_id=commande_id)
    commande.delete()
    messages.success(request, "Commande annulée.")
    return redirect('commandes')


@login_required
def supprimer_compte(request):
    if request.method == 'POST':
        user = request.user
        logout(request)
        user.delete()
        messages.success(request, "Votre compte a été supprimé.")
        return redirect('login')
    return render(request, 'shop/supprimer_compte.html')


# ─── ADMIN CUSTOM ─────────────────────────────────────────────────────────────

@staff_required
def admin_dashboard(request):
    nb_commandes = Commande.objects.count()
    nb_commandes_today = Commande.objects.filter(
        date_commande__date=timezone.now().date()
    ).count()
    nb_plats = Plat.objects.count()
    nb_boissons = Boisson.objects.count()
    nb_utilisateurs = User.objects.count()
    nb_avis = Commentaire.objects.count()
    revenus_total = sum(c.total for c in Commande.objects.filter(paye=True))
    revenus_today = sum(
        c.total for c in Commande.objects.filter(paye=True, date_commande__date=timezone.now().date())
    )
    commandes_recentes = Commande.objects.select_related('utilisateur').order_by('-date_commande')[:8]
    commandes_en_attente = Commande.objects.filter(statut='en_attente').count()
    commandes_en_preparation = Commande.objects.filter(statut='en_preparation').count()
    return render(request, 'shop/admin/dashboard.html', {
        'nb_commandes': nb_commandes,
        'nb_commandes_today': nb_commandes_today,
        'nb_plats': nb_plats,
        'nb_boissons': nb_boissons,
        'nb_utilisateurs': nb_utilisateurs,
        'nb_avis': nb_avis,
        'revenus_total': revenus_total,
        'revenus_today': revenus_today,
        'commandes_recentes': commandes_recentes,
        'commandes_en_attente': commandes_en_attente,
        'commandes_en_preparation': commandes_en_preparation,
    })


@staff_required
def admin_commandes(request):
    statut = request.GET.get('statut', '')
    commandes = Commande.objects.select_related('utilisateur').order_by('-date_commande')
    if statut:
        commandes = commandes.filter(statut=statut)
    return render(request, 'shop/admin/commandes.html', {
        'commandes': commandes,
        'statut_filtre': statut,
        'statuts': Commande.STATUT_CHOICES,
    })


@staff_required
def admin_changer_statut(request, commande_id):
    commande = get_object_or_404(Commande, id=commande_id)
    if request.method == 'POST':
        nouveau_statut = request.POST.get('statut')
        if nouveau_statut in dict(Commande.STATUT_CHOICES):
            commande.statut = nouveau_statut
            commande.save()
            messages.success(request, f"Statut de la commande #{commande_id} mis à jour.")
    return redirect('admin_commandes')


@staff_required
def admin_confirmer_paiement(request, commande_id):
    """Permet à l'admin de confirmer un paiement en espèces."""
    commande = get_object_or_404(Commande, id=commande_id)
    if not commande.paye:
        commande.paye = True
        commande.statut = 'en_preparation'
        commande.save()
        messages.success(request,
            f"✅ Paiement en espèces de la commande #{commande_id} confirmé.")
    return redirect('admin_commandes')


@staff_required
def admin_supprimer_commande(request, commande_id):
    commande = get_object_or_404(Commande, id=commande_id)
    commande.delete()
    messages.success(request, f"Commande #{commande_id} supprimée.")
    return redirect('admin_commandes')


@staff_required
def admin_plats(request):
    plats = Plat.objects.all().order_by('nom')
    return render(request, 'shop/admin/plats.html', {'plats': plats})


@staff_required
def admin_ajouter_plat(request):
    if request.method == 'POST':
        nom = request.POST.get('nom', '').strip()
        prix = request.POST.get('prix', '0')
        categorie = request.POST.get('categorie', '')
        pays = request.POST.get('pays', '')
        disponible = request.POST.get('disponible') == 'on'
        image = request.FILES.get('image')
        if nom and prix:
            plat = Plat.objects.create(
                nom=nom, prix=prix, categorie=categorie,
                pays=pays, disponible=disponible,
            )
            if image:
                plat.image = image
                plat.save()
            messages.success(request, f"Plat « {nom} » ajouté.")
            return redirect('admin_plats')
    return render(request, 'shop/admin/form_plat.html', {
        'categories': Plat.CATEGORIES,
        'pays_choices': [('BF','Burkina Faso'),('TG','Togo'),('CI',"Côte d'Ivoire"),('ML','Mali'),('BJ','Bénin')],
        'action': 'Ajouter',
    })


@staff_required
def admin_modifier_plat(request, plat_id):
    plat = get_object_or_404(Plat, id=plat_id)
    if request.method == 'POST':
        plat.nom = request.POST.get('nom', plat.nom).strip()
        plat.prix = request.POST.get('prix', plat.prix)
        plat.categorie = request.POST.get('categorie', plat.categorie)
        plat.pays = request.POST.get('pays', plat.pays)
        plat.disponible = request.POST.get('disponible') == 'on'
        if request.FILES.get('image'):
            plat.image = request.FILES['image']
        plat.save()
        messages.success(request, f"Plat « {plat.nom} » modifié.")
        return redirect('admin_plats')
    return render(request, 'shop/admin/form_plat.html', {
        'plat': plat,
        'categories': Plat.CATEGORIES,
        'pays_choices': [('BF','Burkina Faso'),('TG','Togo'),('CI',"Côte d'Ivoire"),('ML','Mali'),('BJ','Bénin')],
        'action': 'Modifier',
    })


@staff_required
def admin_supprimer_plat(request, plat_id):
    plat = get_object_or_404(Plat, id=plat_id)
    nom = plat.nom
    plat.delete()
    messages.success(request, f"Plat « {nom} » supprimé.")
    return redirect('admin_plats')


@staff_required
def admin_boissons(request):
    boissons = Boisson.objects.all().order_by('nom')
    return render(request, 'shop/admin/boissons.html', {'boissons': boissons})


@staff_required
def admin_ajouter_boisson(request):
    if request.method == 'POST':
        nom = request.POST.get('nom', '').strip()
        prix = request.POST.get('prix', '0')
        categorie = request.POST.get('categorie', '')
        pays = request.POST.get('pays', '')
        disponible = request.POST.get('disponible') == 'on'
        image = request.FILES.get('image')
        if nom and prix:
            boisson = Boisson.objects.create(
                nom=nom, prix=prix, categorie=categorie,
                pays=pays, disponible=disponible,
            )
            if image:
                boisson.image = image
                boisson.save()
            messages.success(request, f"Boisson « {nom} » ajoutée.")
            return redirect('admin_boissons')
    return render(request, 'shop/admin/form_boisson.html', {
        'categories': Boisson.CATEGORIES,
        'pays_choices': [('BF','Burkina Faso'),('TG','Togo'),('CI',"Côte d'Ivoire"),('ML','Mali'),('BJ','Bénin')],
        'action': 'Ajouter',
    })


@staff_required
def admin_modifier_boisson(request, boisson_id):
    boisson = get_object_or_404(Boisson, id=boisson_id)
    if request.method == 'POST':
        boisson.nom = request.POST.get('nom', boisson.nom).strip()
        boisson.prix = request.POST.get('prix', boisson.prix)
        boisson.categorie = request.POST.get('categorie', boisson.categorie)
        boisson.pays = request.POST.get('pays', boisson.pays)
        boisson.disponible = request.POST.get('disponible') == 'on'
        if request.FILES.get('image'):
            boisson.image = request.FILES['image']
        boisson.save()
        messages.success(request, f"Boisson « {boisson.nom} » modifiée.")
        return redirect('admin_boissons')
    return render(request, 'shop/admin/form_boisson.html', {
        'boisson': boisson,
        'categories': Boisson.CATEGORIES,
        'pays_choices': [('BF','Burkina Faso'),('TG','Togo'),('CI',"Côte d'Ivoire"),('ML','Mali'),('BJ','Bénin')],
        'action': 'Modifier',
    })


@staff_required
def admin_supprimer_boisson(request, boisson_id):
    boisson = get_object_or_404(Boisson, id=boisson_id)
    nom = boisson.nom
    boisson.delete()
    messages.success(request, f"Boisson « {nom} » supprimée.")
    return redirect('admin_boissons')


@staff_required
def admin_avis(request):
    avis = Commentaire.objects.select_related('utilisateur').order_by('-date')
    return render(request, 'shop/admin/avis.html', {'avis': avis})


@staff_required
def admin_supprimer_avis(request, avis_id):
    avis = get_object_or_404(Commentaire, id=avis_id)
    avis.delete()
    messages.success(request, "Avis supprimé.")
    return redirect('admin_avis')


@staff_required
def admin_utilisateurs(request):
    utilisateurs = User.objects.all().order_by('-date_joined')
    return render(request, 'shop/admin/utilisateurs.html', {'utilisateurs': utilisateurs})


@staff_required
def admin_supprimer_utilisateur(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if user == request.user:
        messages.error(request, "Vous ne pouvez pas supprimer votre propre compte.")
        return redirect('admin_utilisateurs')
    username = user.username
    user.delete()
    messages.success(request, f"Utilisateur « {username} » supprimé.")
    return redirect('admin_utilisateurs')