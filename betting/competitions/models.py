from django.db import models

from betting.utils.models import TimeStampedModel


# Create your models here.
class Area(TimeStampedModel):
    src_id = models.PositiveIntegerField()
    name = models.CharField(max_length=128)
    code = models.CharField(max_length=32)
    parent_area = models.ForeignKey('self', on_delete=models.SET_NULL, related_name='child_areas', null=True)


class Season(TimeStampedModel):
    srd_id = models.PositiveIntegerField()
    start_date = models.DateField(null=True)
    end_date = models.DateField(null=True)
    current_match_day = models.PositiveIntegerField(null=True)


class Competition(TimeStampedModel):
    src_id = models.PositiveIntegerField()
    name = models.CharField(max_length=128)
    code = models.CharField(max_length=32, null=True)
    area = models.ForeignKey(Area, on_delete=models.CASCADE, related_name='competitions')
    plan = models.CharField(max_length=64)
    current_season = models.OneToOneField(Season, on_delete=models.SET_NULL, related_name='+', null=True)
    seasons = models.ManyToManyField(Season, related_name='+')


class Team(TimeStampedModel):
    src_id = models.PositiveIntegerField()
    area = models.ForeignKey(Area, on_delete=models.CASCADE, related_name='teams')
    name = models.CharField(max_length=128)
    tla = models.CharField(max_length=16)
    address = models.CharField(max_length=256)
    phone = models.CharField(max_length=64, null=True)
    website = models.URLField(null=True)
    email = models.EmailField(null=True)
    founded = models.PositiveIntegerField()
    colors = models.CharField(max_length=64)
    venue = models.CharField(max_length=64, null=True)
    active_competitions = models.ManyToManyField(Competition, related_name='teams')


class Position(models.Model):
    name = models.CharField(max_length=32)


class Role(models.Model):
    name = models.CharField(max_length=32)


class Member(TimeStampedModel):
    src_id = models.PositiveIntegerField()
    name = models.CharField(max_length=64)
    position = models.ForeignKey(Position, on_delete=models.SET_NULL, related_name='members', null=True)
    date_of_birth = models.DateField(null=True)
    country_of_birth = models.CharField(max_length=64, null=True)
    nationality = models.CharField(max_length=64, null=True)
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='members')
    teams = models.ManyToManyField(Team, related_name='members', blank=True)


class Match(TimeStampedModel):
    src_id = models.PositiveIntegerField()
    competition = models.ForeignKey(Competition, on_delete=models.CASCADE, related_name='matches')
    season = models.ForeignKey(Season, on_delete=models.SET_NULL, null=True)
    start_time = models.DateTimeField()
    status = models.CharField(max_length=32)
    venue = models.CharField(max_length=64)
    match_day = models.PositiveIntegerField()
    stage = models.CharField(max_length=32)
    group = models.CharField(max_length=32)
    home = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='home_matches')
    away = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='away_matches')
    referees = models.ManyToManyField(Member, blank=True)


class Result(TimeStampedModel):
    winner = models.CharField(max_length=32, null=True)
    duration = models.CharField(max_length=32, null=True)
    full_time = models.CharField(max_length=8, null=True)
    half_time = models.CharField(max_length=8, null=True)
    extra_time = models.CharField(max_length=8, null=True)
    penalties = models.CharField(max_length=8, null=True)
    match = models.OneToOneField(Match, on_delete=models.CASCADE, related_name='result')
