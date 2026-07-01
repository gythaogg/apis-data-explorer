from django.db import models

from apis_core.entities.abc import E21_Person, E53_Place, E74_Group
from apis_core.apis_entities.models import AbstractEntity
from apis_core.entities.abc import Entity
from apis_core.generic.abc import GenericModel
from apis_core.relations.models import Relation


class Profession(GenericModel, models.Model):
    name = models.CharField(blank=True, default="", max_length=1024)

    def __str__(self):
        return self.name


class Person(E21_Person, AbstractEntity, Entity):
    profession = models.ManyToManyField(Profession, blank=True)
    bio = models.TextField(blank=True)
    gender = models.CharField(
        max_length=20,
        choices=[
            ("male", "Male"),
            ("female", "Female"),
            ("other", "Other"),
            ("unknown", "Unknown"),
        ],
        default="unknown",
    )


class Place(E53_Place, AbstractEntity, Entity):
    pass


class Group(E74_Group, AbstractEntity, Entity):
    pass


class RelationMixin(Relation):
    certainty = models.CharField(
        max_length=10,
        choices=[
            ("certain", "Certain"),
            ("probable", "Probable"),
            ("uncertain", "Uncertain"),
        ],
        default="certain",
    )

    class Meta:
        abstract = True
        ordering = ["pk"]


class IsCousinOf(RelationMixin):
    subj_model = Person
    obj_model = Person

    @classmethod
    def reverse_name(self) -> str:
        return "is cousin of"


class IsPartOf(RelationMixin):
    subj_model = Person
    obj_model = Group

    @classmethod
    def reverse_name(self) -> str:
        return "consists of"


class IsSiblingOf(RelationMixin):
    subj_model = Person
    obj_model = Person

    @classmethod
    def reverse_name(self) -> str:
        return "is sibling of"


class LivesIn(RelationMixin):
    subj_model = Person
    obj_model = Place

    @classmethod
    def reverse_name(self) -> str:
        return "has inhabitant"


class IsParentOf(RelationMixin):
    subj_model = Person
    obj_model = Person

    @classmethod
    def reverse_name(self) -> str:
        return "is child of"
