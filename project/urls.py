# urls.py
from django.contrib import admin
from django.urls import path, include
#from accounting.custom_admin import CustomAdminSite
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from accounting.models import Invoice, Client, Supplier, Product, Payment
from accounting.admin import custom_admin_site  # Adjust the import path based on your app structure
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns

#custom_admin_site = CustomAdminSite(name='custom_admin')

# Register your models to the new admin site
# custom_admin_site.register(get_user_model())
# custom_admin_site.register(Group)
# custom_admin_site.register(Invoice)
# custom_admin_site.register(Client)
# custom_admin_site.register(Product)
# custom_admin_site.register(Supplier)
# custom_admin_site.register(Payment)

urlpatterns = [
    path('i18n/', include('django.conf.urls.i18n')),  # Language switcher
] + i18n_patterns(
    path('admin/', custom_admin_site.urls),
    prefix_default_language=True

)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)