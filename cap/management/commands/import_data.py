import os
import csv
from django.core.management.base import BaseCommand
from cap.models import Hotel, Flight, Tour

class Command(BaseCommand):
    help = 'Import data from CSV files into the database'

    def handle(self, *args, **kwargs):
        base_path = os.path.join(os.path.dirname(__file__), '../../data/')

        # Import Hotels
        hotel_file = os.path.join(base_path, 'hotel_clean_new.csv')
        with open(hotel_file, encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                Hotel.objects.create(**row)
        self.stdout.write(self.style.SUCCESS('Successfully imported hotels'))

        # Import Flights
        flight_file = os.path.join(base_path, 'plane_clean.csv')
        with open(flight_file, encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                Flight.objects.create(**row)
        self.stdout.write(self.style.SUCCESS('Successfully imported flights'))

        # Import Tours
        tour_file = os.path.join(base_path, 'tour_clean.csv')
        with open(tour_file, encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                
                Tour.objects.create(**row)
        self.stdout.write(self.style.SUCCESS('Successfully imported tours'))
