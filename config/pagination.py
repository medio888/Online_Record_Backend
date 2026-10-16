from rest_framework.pagination import PageNumberPagination


class StandardPagination(PageNumberPagination):
    """Постраничный вывод длинных списков (обращения, записи).

    Формат ответа:
    {"count": 45, "next": "...?page=2", "previous": null, "results": [...]}

    Параметры запроса: ?page=2 и ?page_size=10 (максимум 100).
    """

    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100