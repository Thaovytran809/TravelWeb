from django.db import models


class Hotel(models.Model):
    hotel_name = models.CharField(max_length=255)
    location = models.CharField(max_length=255)
    price = models.FloatField()
    score_hotels = models.CharField(max_length=100, null=True, blank=True)
    number_rating = models.FloatField(null=True, blank=True)
    star_number = models.IntegerField(null=True, blank=True)
    received_time = models.CharField(max_length=255)
    giveback_time = models.CharField(max_length=255)
    from_center = models.CharField(max_length=100, null=True, blank=True)
    popular_destination = models.CharField(max_length=255)
    hotel_link = models.URLField()
    hotel_city = models.CharField(max_length=255)
    hotel_id = models.CharField(max_length=50, unique=True)
    start_clean = models.CharField(max_length=255)

    def __str__(self):
        return self.hotel_name

class Flight(models.Model):
    Airline = models.CharField(max_length=255)
    Price = models.FloatField()
    Start_Day = models.CharField(max_length=255)
    Start_time = models.CharField(max_length=255)
    take_place = models.CharField(max_length=255)
    End_time = models.CharField(max_length=255)
    destination = models.CharField(max_length=255)
    flight_time = models.CharField(max_length=255,null=True, blank=True)
    transit = models.CharField(max_length=255)
    total_time_hour = models.FloatField(null=True, blank=True)
    End_day = models.CharField(max_length=255)
    Is_Transit = models.BooleanField()
    Is_VietJet_Air = models.BooleanField()
    Is_Vietnam_Airlines = models.BooleanField()
    Is_Bamboo_Airways = models.BooleanField()
    Is_Vietravel_Airlines = models.BooleanField()
    Id_Plane = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.Airline

class Tour(models.Model):
    tour_name = models.CharField(max_length=255)
    location = models.CharField(max_length=255)
    price = models.FloatField()
    duration = models.CharField(max_length=255,null=True, blank=True)
    rating = models.CharField(max_length=50, null=True, blank=True)
    City = models.CharField(max_length=255)
    tour_id = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.tour_name
