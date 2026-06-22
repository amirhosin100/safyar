import json
import re
from typing import Any, Iterable

from django.contrib.postgres.aggregates import StringAgg
from django.core.exceptions import FieldDoesNotExist
from django.db.models import BooleanField, Case, CharField, F, Q, Value, When
from django.db.models.functions import Cast, Coalesce
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import BaseFilterBackend, OrderingFilter, SearchFilter

DISPLAY_LABEL_FIELD_CANDIDATES = (
    "display_label",
    "label",
    "name",
    "title",
    "username",
    "full_name",
    "code",
    "slug",
    "plate",
    "license_plate",
    "identifier",
    "factor_number",
    "serial_number",
)

MRT_FILTER_PARAMS = ("mrt_filters", "filters", "column_filters")
MRT_FILTER_MODE_PARAMS = ("mrt_filter_modes", "filter_modes", "column_filter_modes")
MRT_GROUPING_PARAMS = ("grouping", "mrt_grouping")


def _get_query_param(request, names: Iterable[str]) -> str | None:
    for name in names:
        value = request.query_params.get(name)
        if value not in (None, ""):
            return value
    return None


def _loads_json(value: str | None, fallback: Any) -> Any:
    if not value:
        return fallback
    try:
        return json.loads(value)
    except (TypeError, ValueError):
        return fallback


def _parse_column_list(value: str | None) -> list[str]:
    if not value:
        return []
    decoded = _loads_json(value, None)
    if isinstance(decoded, list):
        return [str(item) for item in decoded if item not in (None, "")]
    return [part for part in (p.strip() for p in value.split(",")) if part]


def _parse_column_filters(request) -> list[dict[str, Any]]:
    raw = _get_query_param(request, MRT_FILTER_PARAMS)
    decoded = _loads_json(raw, [])
    if isinstance(decoded, dict):
        return [
            {"id": key, "value": value}
            for key, value in decoded.items()
            if key and value not in (None, "")
        ]
    if not isinstance(decoded, list):
        return []
    filters: list[dict[str, Any]] = []
    for item in decoded:
        if not isinstance(item, dict):
            continue
        column_id = item.get("id")
        value = item.get("value")
        if column_id and value not in (None, ""):
            filters.append({"id": str(column_id), "value": value})
    return filters


def _parse_filter_modes(request) -> dict[str, str]:
    decoded = _loads_json(_get_query_param(request, MRT_FILTER_MODE_PARAMS), {})
    if not isinstance(decoded, dict):
        return {}
    return {str(key): str(value) for key, value in decoded.items()}


def _safe_annotation_name(column_name: str) -> str:
    safe = re.sub(r"[^0-9a-zA-Z_]+", "_", column_name).strip("_")
    return f"_mrt_display_{safe[:40]}"


def _normalise_column_name(column_name: str) -> str:
    if column_name.endswith("_display"):
        column_name = column_name[: -len("_display")]
    return column_name.replace(".", "__")


def _serializer_column_names(view) -> set[str]:
    try:
        serializer = view.get_serializer_class()(context=view.get_serializer_context())
    except Exception:
        try:
            serializer = view.get_serializer_class()()
        except Exception:
            return set()
    return {
        name
        for name, field in serializer.fields.items()
        if not getattr(field, "write_only", False)
    }


def _model_field(model, field_name: str):
    try:
        return model._meta.get_field(field_name)
    except FieldDoesNotExist:
        return None


def _has_model_field(model, field_name: str) -> bool:
    return _model_field(model, field_name) is not None


def _is_allowed_column(queryset, view, column_name: str) -> bool:
    column_name = _normalise_column_name(column_name)
    if column_name in queryset.query.annotations:
        return True
    if column_name in _serializer_column_names(view):
        return True
    root = column_name.split("__", 1)[0]
    return _has_model_field(queryset.model, root)


def _choice_display_expression(field_name: str, model_field) -> Case:
    cases = [
        When(**{field_name: value}, then=Value(str(label)))
        for value, label in getattr(model_field, "choices", [])
    ]
    return Case(
        *cases,
        default=Cast(F(field_name), output_field=CharField()),
        output_field=CharField(),
    )


def _boolean_display_expression(field_name: str) -> Case:
    return Case(
        When(**{field_name: True}, then=Value("بله")),
        When(**{field_name: False}, then=Value("خیر")),
        default=Value("-"),
        output_field=CharField(),
    )


def _relation_display_expression(prefix: str, related_model) -> Coalesce:
    expressions = []
    for candidate in DISPLAY_LABEL_FIELD_CANDIDATES:
        if candidate == "display_label" or not _has_model_field(
            related_model, candidate
        ):
            continue
        expressions.append(Cast(F(f"{prefix}__{candidate}"), output_field=CharField()))

    pk_name = related_model._meta.pk.name
    expressions.append(Cast(F(f"{prefix}__{pk_name}"), output_field=CharField()))
    return Coalesce(*expressions, Value(""), output_field=CharField())


def _custom_display_expression(queryset, view, column_name: str):
    custom_getter = getattr(view, "get_mrt_display_expression", None)
    if callable(custom_getter):
        expression = custom_getter(column_name, queryset)
        if expression is not None:
            return expression

    custom_map = getattr(view, "mrt_display_expressions", None)
    if isinstance(custom_map, dict):
        expression = custom_map.get(column_name)
        if expression is not None:
            return expression
    return None


def _display_expression(queryset, view, column_name: str):
    column_name = _normalise_column_name(column_name)

    custom_expression = _custom_display_expression(queryset, view, column_name)
    if custom_expression is not None:
        return custom_expression

    if column_name in queryset.query.annotations:
        return Cast(F(column_name), output_field=CharField())

    model_field = _model_field(queryset.model, column_name)
    if model_field is None:
        return None

    if getattr(model_field, "choices", None):
        return _choice_display_expression(column_name, model_field)

    if isinstance(model_field, BooleanField):
        return _boolean_display_expression(column_name)

    related_model = getattr(model_field, "related_model", None)
    if related_model is not None and getattr(model_field, "many_to_many", False):
        return StringAgg(
            _relation_display_expression(column_name, related_model),
            delimiter="، ",
            distinct=True,
            output_field=CharField(),
        )

    if related_model is not None and getattr(model_field, "is_relation", False):
        return _relation_display_expression(column_name, related_model)

    return Cast(F(column_name), output_field=CharField())


def _ordering_field(queryset, view, column_name: str) -> tuple[Any, bool]:
    column_name = _normalise_column_name(column_name)
    model_field = _model_field(queryset.model, column_name)
    if (
        model_field is not None
        and not getattr(model_field, "choices", None)
        and not isinstance(model_field, BooleanField)
        and not getattr(model_field, "is_relation", False)
    ):
        return column_name, False

    return _display_expression(queryset, view, column_name), True


def _ensure_display_annotation(queryset, view, column_name: str):
    if not _is_allowed_column(queryset, view, column_name):
        return queryset, None

    normalised = _normalise_column_name(column_name)
    annotation_name = _safe_annotation_name(normalised)
    if annotation_name in queryset.query.annotations:
        return queryset, annotation_name

    expression = _display_expression(queryset, view, normalised)
    if expression is None:
        return queryset, None
    return queryset.annotate(**{annotation_name: expression}), annotation_name


def _filter_lookup(annotation_name: str, mode: str, value: Any) -> Q:
    mode = mode or "contains"
    text = str(value)
    if mode in {"equals", "equalsString"}:
        return Q(**{f"{annotation_name}__iexact": text})
    if mode == "notEquals":
        return ~Q(**{f"{annotation_name}__iexact": text})
    if mode == "startsWith":
        return Q(**{f"{annotation_name}__istartswith": text})
    if mode == "endsWith":
        return Q(**{f"{annotation_name}__iendswith": text})
    if mode == "empty":
        return Q(**{f"{annotation_name}__in": ["", "-"]})
    if mode == "notEmpty":
        return ~Q(**{f"{annotation_name}__in": ["", "-"]})
    return Q(**{f"{annotation_name}__icontains": text})


def _filter_values_lookup(annotation_name: str, mode: str, value: Any) -> Q:
    if isinstance(value, list):
        conditions = [_filter_lookup(annotation_name, mode, item) for item in value]
        if not conditions:
            return Q()
        q_object = Q()
        for condition in conditions:
            q_object = (
                q_object & condition
                if mode == "arrIncludesAll"
                else q_object | condition
            )
        return q_object
    return _filter_lookup(annotation_name, mode, value)


class CustomSearchFilter(SearchFilter):
    filterable_types = ["CharField", "TextField"]
    forbidden_fields = ["password"]

    def get_search_fields(self, view, request):
        if hasattr(view, "search_fields") and view.search_fields:
            return view.search_fields
        else:
            current_model = view.get_queryset().model
            model_fields = current_model._meta.get_fields()

            database_fields = [
                field.name
                for field in model_fields
                if field.get_internal_type() in self.filterable_types
                and field.name not in self.forbidden_fields
            ]

            # annotated_fields = [
            #     key for key in queryset.query.annotations.keys()
            #     if queryset.query.annotations[key].output_field.get_internal_type() in self.filterable_types
            # ]

            return database_fields  # + annotated_fields

    def filter_queryset(self, request, queryset, view):
        queryset = self.filter_mrt_column_filters(request, queryset, view)

        search_fields = getattr(view, "search_fields", None)
        search_query = request.query_params.get(self.search_param, "")

        if not search_fields and search_query:
            q_object = Q()
            for field in _serializer_column_names(view):
                queryset, annotation_name = _ensure_display_annotation(
                    queryset, view, field
                )
                if annotation_name is not None:
                    q_object |= Q(**{f"{annotation_name}__icontains": search_query})
            return queryset.filter(q_object) if q_object else queryset

        if search_fields and search_query:
            q_object = Q()
            for field in search_fields:
                if "__display" in field:
                    field_name = field.replace("__display", "")
                    if field_name in queryset.query.annotations:
                        annotation_subquery = queryset.query.annotations[field_name]
                        if (
                            hasattr(annotation_subquery, "field")
                            and annotation_subquery.field.choices
                        ):
                            choices_dict = dict(annotation_subquery.field.choices)
                        else:
                            continue
                    else:
                        try:
                            model_field = queryset.model._meta.get_field(field_name)
                            if hasattr(model_field, "choices"):
                                choices_dict = dict(model_field.choices)
                            else:
                                continue
                        except FieldDoesNotExist:
                            continue

                    reverse_mapping = {v: k for k, v in choices_dict.items()}
                    if search_query in reverse_mapping:
                        q_object |= Q(**{field_name: reverse_mapping[search_query]})
                else:
                    q_object |= Q(**{f"{field}__icontains": search_query})
            return queryset.filter(q_object)

        return super().filter_queryset(request, queryset, view)

    def filter_mrt_column_filters(self, request, queryset, view):
        filters = _parse_column_filters(request)
        if not filters:
            return queryset

        filter_modes = _parse_filter_modes(request)
        for item in filters:
            column_id = item["id"]
            queryset, annotation_name = _ensure_display_annotation(
                queryset, view, column_id
            )
            if annotation_name is None:
                continue
            mode = filter_modes.get(column_id, "contains")
            queryset = queryset.filter(
                _filter_values_lookup(annotation_name, mode, item["value"])
            )
        return queryset


class CustomOrderingFilter(OrderingFilter):
    def filter_queryset(self, request, queryset, view):
        ordering = self.get_ordering(request, queryset, view)
        if not ordering:
            return queryset

        resolved_ordering = []
        for field_name in ordering:
            descending = field_name.startswith("-")
            column_name = field_name[1:] if descending else field_name
            if not _is_allowed_column(queryset, view, column_name):
                continue

            resolved, needs_annotation = _ordering_field(queryset, view, column_name)
            if resolved is None:
                continue
            if needs_annotation:
                annotation_name = _safe_annotation_name(
                    _normalise_column_name(column_name)
                )
                queryset = queryset.annotate(**{annotation_name: resolved})
                resolved_ordering.append(
                    f"-{annotation_name}" if descending else annotation_name
                )
            else:
                resolved_ordering.append(f"-{resolved}" if descending else resolved)

        return queryset.order_by(*resolved_ordering) if resolved_ordering else queryset


class CustomGroupingFilter(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        grouping = _parse_column_list(_get_query_param(request, MRT_GROUPING_PARAMS))
        if not grouping:
            return queryset

        group_ordering = []
        for column_name in grouping:
            queryset, annotation_name = _ensure_display_annotation(
                queryset, view, column_name
            )
            if annotation_name is not None:
                group_ordering.append(annotation_name)

        if not group_ordering:
            return queryset

        existing_ordering = tuple(queryset.query.order_by or ())
        return queryset.order_by(*group_ordering, *existing_ordering)


class CustomFilterSetFilter(DjangoFilterBackend):
    filterable_types = [
        "CharField",
        "TextField",
        "BigAutoField",
        "PositiveSmallIntegerField",
        "DateTimeField",
        "SmallIntegerField",
        "IntegerField",
        "BooleanField",
    ]
    forbidden_fields = ["password", "work_days"]

    def get_filterset_class(self, view, queryset=None):
        if not hasattr(view, "filterset_fields") or not view.filterset_fields:
            temp_queryset = view.get_queryset() if queryset is None else queryset
            current_model = temp_queryset.model
            model_fields = current_model._meta.get_fields()
            filter_specs: dict[str, list[str]] = {}
            for field in model_fields:
                if not hasattr(field, "get_internal_type"):
                    continue
                try:
                    internal = field.get_internal_type()
                except AttributeError:
                    continue
                if (
                    internal not in self.filterable_types
                    or field.name in self.forbidden_fields
                ):
                    continue
                if internal == "DateTimeField":
                    filter_specs[field.name] = ["exact", "gte", "lte", "date"]
                else:
                    filter_specs[field.name] = ["exact"]
            view.filterset_fields = filter_specs
        return super().get_filterset_class(view, queryset)
