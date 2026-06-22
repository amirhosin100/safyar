from rest_framework.pagination import PageNumberPagination


class CustomPageNumberPagination(PageNumberPagination):
    page_size = 15
    page_size_query_param = "page_size"
    max_page_size = 1000


class OptionalPageNumberPagination(CustomPageNumberPagination):
    """
    Only paginate when the client sends ?page=… and/or ?page_size=… .
    Otherwise list returns the full queryset (legacy behavior for getAll()).
    """

    def paginate_queryset(self, queryset, request, view=None):
        qp = getattr(request, "query_params", request.GET)
        if self.page_size_query_param not in qp and self.page_query_param not in qp:
            return None
        return super().paginate_queryset(queryset, request, view)
