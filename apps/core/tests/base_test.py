import abc
import copy
import functools
import importlib
from typing import Type

import pytest
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models import ManyToManyField
from django.urls import reverse
from rest_framework import status
from apps.core.models import BaseModel
from apps.core.utils.get_detail_url_resolver import get_detail_url_resolver
from apps.core.utils.snake_case import get_model_name_snake_case


class RequestDataDescriptor:
    def __set_name__(self, owner, name):
        self.name = name

    def __get__(self, instance, owner):
        instance.__dict__.setdefault("run_function", False)

        if instance is None:
            return self
        if not isinstance(instance, Data):
            raise ValueError("You just can use RequestDataDescriptor in Data class")

        if not instance.__dict__["run_function"]:
            instance.__dict__["run_function"] = True
            instance._run_functions()

        return instance.__dict__.get(self.name)

    def __set__(self, instance, value):
        instance.__dict__[self.name] = value


class Data(abc.ABC):
    request_data = RequestDataDescriptor()

    def __init__(
        self,
        model: Type[BaseModel],
        request_data: dict,
        response_data: dict = None,
        extra_fields: list = ["id", "created_at", "updated_at"],
        relation_fields: dict = {},
        dependencies: list = [],
    ) -> None:
        self.request_data = request_data
        self.response_data = (
            response_data if response_data is not None else copy.deepcopy(request_data)
        )
        self.extra_fields = extra_fields
        self.relation_fields = relation_fields
        self.dependencies = dependencies
        self._model = model

        self._many_to_many_fields = {}

    def _run_functions(self):
        for key, value in self.request_data.items():
            if isinstance(value, functools.partial):
                self.request_data[key] = value()

    def set_model(self, model):
        self._model = model

    def check_response(self, response: dict):
        for field in self.extra_fields:
            assert field in response
            response.pop(field)

        # checking choice fields
        display_fields = [field for field in response if field.endswith("_display")]

        for display_field in display_fields:
            original_field_name = display_field.split("_display")[0]
            choices = dict(self._model._meta.get_field(original_field_name).choices)

            # if field in response is not empty
            if response[original_field_name]:
                display_name = choices[response[original_field_name]]
                assert response[display_field] == display_name

            response.pop(display_field)

        # ignore display_label field
        response.pop("display_label")

        assert response == self.response_data

    def create_object(self, get_or_create=False):
        self.set_up(get_or_create)
        if get_or_create:
            obj, _ = self._model.objects.get_or_create(**self.request_data)
        else:
            obj = self._model.objects.create(**self.request_data)
        # adding many to many fields to object
        for field, instance in self._many_to_many_fields.items():
            field = getattr(obj, field)
            field.set([instance])
        obj.save()

        return obj

    def _create_dependencies(self, get_or_create=False):
        for dependency in self.dependencies:
            dependency.create_object(get_or_create)
        return True

    @abc.abstractmethod
    def _create_relation_fields(self, get_or_create):
        pass

    def set_up(self, get_or_create=False):
        self._run_functions()
        self._create_relation_fields(get_or_create)
        self._create_dependencies(get_or_create)


class InitialData(Data):
    def _create_relation_fields(self, get_or_create):
        for field, dependency in self.relation_fields.items():
            dependency_obj = dependency.create_object(get_or_create)

            if isinstance(self._model._meta.get_field(field), ManyToManyField):
                self._many_to_many_fields[field] = dependency_obj
            else:
                self.request_data[field] = dependency_obj


class APIRequestData(Data):
    def _create_relation_fields(self, get_or_create):
        for field, dependency in self.relation_fields.items():
            dependency_obj = dependency.create_object(get_or_create)

            if isinstance(self._model._meta.get_field(field), ManyToManyField):
                self.request_data[field] = [dependency_obj.pk]
            else:
                self.request_data[field] = dependency_obj.pk


def get_content_type_id(model):
    return ContentType.objects.get_for_model(model).pk


@pytest.mark.django_db
class BaseTest:
    app_name = ""
    model: type[models.Model] | None = None
    create_data: APIRequestData | None = None
    update_data: APIRequestData | None = None
    initial_data: InitialData | None = None

    def initialize_data(self):
        self._model_name = self.model._meta.model_name
        self.app_name = self.model._meta.app_label

        prefix = get_model_name_snake_case(self.model.__name__)

        data = importlib.import_module(f"apps.{self.app_name}.tests.fixtures.data")
        data = importlib.reload(data)
        self.initial_data = getattr(data, f"{prefix}_initial_data", None)
        self.create_data = getattr(data, f"{prefix}_create_data", None)
        self.update_data = getattr(data, f"{prefix}_update_data", None)

        if self.update_data is None:
            self.update_data = copy.deepcopy(self.create_data)

        if self.create_data is None or self.initial_data is None:
            raise ValueError(
                f"You have to write the `{prefix}_initial_data` and"
                f"`{prefix}_create_data` variables into "
                f"{self.app_name}.tests.fixtures.data module."
            )

    @staticmethod
    def get_urls(model):
        """
        returns list-create and delete-detail-update urls
        """
        model_name = model._meta.model_name
        app_name = model._meta.app_label

        detail_update_delete_url = get_detail_url_resolver(app_name, model_name)
        list_create_url = reverse(f"{app_name}-{model_name}-list")

        return detail_update_delete_url, list_create_url


class BaseTestView(BaseTest):

    @pytest.fixture(autouse=True)
    def initialize_data(self):
        super().initialize_data()
        urls = self.get_urls(self.model)
        self.detail_update_delete_url = urls[0]
        self.list_create_url = urls[1]

    def test_detail(self, api_client):
        obj = self.initial_data.create_object()
        response = api_client.get(self.detail_update_delete_url(obj.pk))

        assert response.status_code == status.HTTP_200_OK
        self.initial_data.check_response(response.data)

    def test_list(self, api_client):
        count = self.model.objects.count()
        self.initial_data.create_object()

        response = api_client.get(self.list_create_url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == count + 1

    def test_create(self, api_client):
        count = self.model.objects.count()
        self.create_data.set_up()
        response = api_client.post(
            self.list_create_url, data=self.create_data.request_data, format="multipart"
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert self.model.objects.count() == count + 1
        self.create_data.check_response(response.data)

    def test_update(self, api_client):
        obj = self.initial_data.create_object()

        response = api_client.patch(
            self.detail_update_delete_url(obj.pk),
            data=self.update_data.request_data,
        )

        assert response.status_code == status.HTTP_200_OK
        self.update_data.check_response(response.data)

    def test_delete(self, api_client):
        obj = self.initial_data.create_object()
        count = self.model.objects.count()

        response = api_client.delete(self.detail_update_delete_url(obj.pk))

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert self.model.objects.count() == count - 1

        with pytest.raises(self.model.DoesNotExist):
            self.model.objects.get(pk=obj.pk)


class BaseTestModel(BaseTest):
    @pytest.fixture(autouse=True)
    def initialize_data(self):
        super().initialize_data()
