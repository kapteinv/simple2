import os

from django.db import models
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse

from autoslug import AutoSlugField
from gnupg import GPG
from PIL import Image
from shops.utils import create_thumb, has_changed


class Account(models.Model):

    # admin_msg alert choices
    SUCCESS = 'success'
    INFO = 'info'
    WARNING = 'warning'
    DANGER = 'danger'
    ALERT_CHOICES = (
        (SUCCESS, 'success'),
        (INFO, 'info'),
        (WARNING, 'warning'),
        (DANGER, 'danger'),
    )

    # absence choices
    DISPONIBLE = 'disponible'
    ABSENT = 'absent'
    INDISPONIBLE = 'indisponible'
    RUPTURE = 'en rupture de stock'
    VACANCES = 'en vacances'
    ABSENCE_CHOICES = (
        (DISPONIBLE, 'disponible'),
        (ABSENT, 'absent'),
        (INDISPONIBLE, 'indisponible'),
        (RUPTURE, 'en rupture de stock'),
        (VACANCES, 'en vacances'),
    )

    user = models.OneToOneField(User, unique=True)
    slug = AutoSlugField(populate_from='user', unique=True)
    avatar = models.ImageField(upload_to='media/profile_avatar', blank=True)
    fdw_identity = models.CharField(max_length=20, blank=True, default='')
    fdw_id = models.PositiveIntegerField(default=0)
    email = models.EmailField(max_length=254, blank=True, default='')
    jid = models.EmailField(max_length=254, default='@libertygb2nyeyay.onion')
    gpg = models.TextField(
        blank=True,
        default='',
        verbose_name="Entrez ici votre clé GPG publique :"
    )
    btc = models.CharField(max_length=50, blank=True, default='')
    irc = models.CharField(max_length=20, blank=True, default='')
    ricochet = models.CharField(max_length=50, blank=True, default='')
    bitmessage = models.CharField(max_length=50, blank=True, default='')
    description = models.TextField(
        blank=True,
        default='',
        verbose_name="Description du profil :"
    )
    absence = models.CharField(
        max_length=20,
        choices=ABSENCE_CHOICES,
        default=DISPONIBLE,
        verbose_name="Saisissez ici un motif pour activer le mode absence"
    )
    affich_ligne = models.BooleanField(
        default=False,
        verbose_name="Cochez cette case pour basculer vers l'affichage ligne"
    )
    admin_msg = models.TextField(
        max_length=300,
        verbose_name="Message du staff", blank=True, default=''
    )
    alert = models.CharField(
        max_length=10,
        choices=ALERT_CHOICES,
        default=DANGER
    )
    escrow_msg = models.TextField(
        max_length=300,
        verbose_name="Message personnel de l'escrow",
        blank=True, default=''
    )
    updated_at = models.DateTimeField(auto_now=True)
    banned = models.BooleanField(default=False)
    inactive = models.BooleanField(default=False)


    def get_absolute_url(self):
        return reverse('profile', kwargs={'slug': self.slug})

    @property
    def nbre_feeds(self):
        return self.user.feedback.all().count()

    @property
    def likes(self):
        return self.user.feedback.filter(positive=True).count()

    @property
    def unlikes(self):
        return self.user.feedback.filter(positive=False).count()

    @property
    def average(self):
        try:
            average = round((self.likes / self.nbre_feeds) * 100, 2)
        except ZeroDivisionError:
            average = 0
        return average

    @property
    def fingerprint(self):
        gpg = GPG()
        gpg.encoding = "utf-8"
        try:
            fingerprint = gpg.import_keys(self.gpg).fingerprints[0]
        except IndexError:
            fingerprint = ""
        return fingerprint

    def save(self, *args, **kwargs):
        if has_changed(self, 'avatar'):
            # on va convertir l'image en jpg
            f, e = os.path.splitext(str(self.avatar.name))
            filename = "{}.jpg".format(f)

            # Ne fait rien si pas d'image
            try:
                image = Image.open(self.avatar.file)

                if image.mode not in ('L', 'RGB'):
                    image = image.convert('RGB')

                # pré-sauvegarde de la photo modifié
                self.avatar.save(
                    filename,
                    create_thumb(image, (250, 250)),
                    save=False
                )
            except ValueError:
                pass

        super(Account, self).save(*args, **kwargs)

    def __str__(self):
        return str(self.slug)
