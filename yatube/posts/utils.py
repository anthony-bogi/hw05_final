from django.core.paginator import Paginator
from .constants import POSTS_PER_PAGE


def paginator_def(request, post_obj):
    paginator = Paginator(post_obj, POSTS_PER_PAGE)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)
