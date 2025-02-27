# utils/helpers.py
from typing import Any, Dict
from django.core.paginator import Paginator


def paginate_queryset(queryset, page: int, page_size: int) -> Dict[str, Any]:
    paginator = Paginator(queryset, page_size)
    page_obj = paginator.get_page(page)

    return {
        'items': page_obj.object_list,
        'total': paginator.count,
        'pages': paginator.num_pages,
        'current_page': page_obj.number,
        'has_next': page_obj.has_next(),
        'has_previous': page_obj.has_previous(),
    }