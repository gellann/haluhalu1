# core/context_processors.py
from .models import Product

def categories_processor(request):
    """
    Context processor to make a list of unique product categories available
    to all templates.
    """
    # Get unique categories from the Product model
    unique_categories = Product.objects.values_list('category', flat=True).distinct().order_by('category')
    return {'categories': unique_categories}