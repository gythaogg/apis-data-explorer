from __future__ import annotations

import random

from django.core.management.base import BaseCommand
from django.db import transaction

from faker import Faker

from sample_project.models import (
    Group,
    IsCousinOf,
    IsParentOf,
    IsPartOf,
    IsSiblingOf,
    LivesIn,
    Person,
    Place,
    Profession,
)
from django.contrib.contenttypes.models import ContentType


class Command(BaseCommand):
    help = "Populate sample_project models with realistic demo data"

    def add_arguments(self, parser):
        parser.add_argument(
            "--people",
            type=int,
            default=25,
            help="Number of people to generate (default: 25)",
        )
        parser.add_argument(
            "--seed",
            type=int,
            default=42,
            help="Random seed for deterministic output (default: 42)",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        people_count = max(0, options["people"])
        seed = options["seed"]

        content_types = {
            "person": ContentType.objects.get_for_model(Person),
            "place": ContentType.objects.get_for_model(Place),
            "group": ContentType.objects.get_for_model(Group),
        }

        random.seed(seed)
        fake = Faker()
        fake.seed_instance(seed)

        profession_names = [
            "Carpenter",
            "Merchant",
            "Teacher",
            "Engineer",
            "Artist",
            "Archivist",
            "Librarian",
            "Farmer",
            "Blacksmith",
            "Scholar",
        ]
        place_names = [
            "Vienna",
            "Graz",
            "Linz",
            "Salzburg",
            "Innsbruck",
            "Prague",
            "Brno",
            "Budapest",
            "Krakow",
            "Ljubljana",
        ]
        group_names = [
            "Guild of Craftsmen",
            "Circle of Scholars",
            "Merchant House Adler",
            "Town Council",
            "Writers Collective",
        ]

        professions = [
            Profession.objects.get_or_create(name=name)[0] for name in profession_names
        ]
        places = [Place.objects.get_or_create(label=name)[0] for name in place_names]
        groups = [Group.objects.get_or_create(label=name)[0] for name in group_names]

        people = []
        genders = ["male", "female", "other", "unknown"]

        for _ in range(people_count):
            forename = fake.first_name()
            surname = fake.last_name()  
            person, _ = Person.objects.get_or_create(
                forename=forename,
                surname=surname,
                defaults={
                    "bio": fake.paragraph(nb_sentences=3),
                    "gender": random.choice(genders),
                },
            )

            if not person.bio:
                person.bio = fake.paragraph(nb_sentences=3)
            if person.gender == "unknown":
                person.gender = random.choice(genders)
            person.save(update_fields=["bio", "gender"])

            person.profession.set(random.sample(professions, k=random.randint(1, 3)))
            people.append(person)

        certainties = ["certain", "probable", "uncertain"]

        for person in people:
            place = random.choice(places)
            LivesIn.objects.get_or_create(
                subj_object_id=person.pk,
                obj_object_id=place.pk,
                subj_content_type=content_types["person"],
                obj_content_type=content_types["place"],
                defaults={"certainty": random.choice(certainties)},
            )

            group = random.choice(groups)
            IsPartOf.objects.get_or_create(
                subj_object_id=person.pk,
                obj_object_id=group.pk,
                subj_content_type=content_types["person"],
                obj_content_type=content_types["group"],
                defaults={"certainty": random.choice(certainties)},
            )

        if len(people) > 1:
            shuffled = people[:]
            random.shuffle(shuffled)

            pair_count = len(shuffled) // 2
            for idx in range(pair_count):
                p1 = shuffled[idx * 2]
                p2 = shuffled[idx * 2 + 1]
                if p1.pk == p2.pk:
                    continue
                IsSiblingOf.objects.get_or_create(
                    subj_object_id=p1.pk,
                    obj_object_id=p2.pk,
                    subj_content_type=content_types["person"],
                    obj_content_type=content_types["person"],
                    defaults={"certainty": random.choice(certainties)},
                )

            for _ in range(min(people_count // 3, len(people) // 2)):
                parent, child = random.sample(people, 2)
                if parent.pk == child.pk:
                    continue
                IsParentOf.objects.get_or_create(
                    subj_object_id=parent.pk,
                    obj_object_id=child.pk,
                    subj_content_type=content_types["person"],
                    obj_content_type=content_types["person"],
                    defaults={"certainty": random.choice(certainties)},
                )

            for _ in range(min(people_count // 4, len(people) // 2)):
                p1, p2 = random.sample(people, 2)
                if p1.pk == p2.pk:
                    continue
                IsCousinOf.objects.get_or_create(
                    subj_object_id=p1.pk,
                    obj_object_id=p2.pk,
                    subj_content_type=content_types["person"],
                    obj_content_type=content_types["person"],
                    defaults={"certainty": random.choice(certainties)},
                )

        self.stdout.write(self.style.SUCCESS("Sample data population completed."))
        self.stdout.write(
            f"People: {Person.objects.count()}, Places: {Place.objects.count()}, "
            f"Groups: {Group.objects.count()}, Professions: {Profession.objects.count()}"
        )
