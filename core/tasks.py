from celery import shared_task
from .models import UserCharater
from django.utils import timezone

@shared_task
def regenerate_energy():
    print("Regenerate energy task started")
    for character in UserCharater.objects.all():
        if character.engry < 1000:
            minutes_passed = int((timezone.now() - character.last_energy_update).total_seconds() // 60)
            print(f"Checking character {character.id}: energy={character.engry}, minutes_passed={minutes_passed}")
            if minutes_passed > 0:
                new_energy = min(character.engry + minutes_passed, 1000)
                print(f"Updating character {character.id} energy from {character.engry} to {new_energy}")
                character.engry = new_energy
                character.last_energy_update = timezone.now()
                character.save()
    print("Regenerate energy task finished")
