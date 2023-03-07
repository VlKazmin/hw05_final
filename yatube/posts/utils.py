from django.core.paginator import Paginator


def paginate(request, *args, **kwargs):
    paginator = Paginator(*args, **kwargs)
    page_number = request.GET.get("page")
    return paginator.get_page(page_number)
