import datetime
import environ
import os
import re
import requests
import time

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
import django

django.setup()
from betting.competitions.models import Area, Season, Competition, Team, Member, Position, Role

ROOT_DIR = environ.Path(__file__)
env = environ.Env()
env.read_env(str(ROOT_DIR.path('.env')))

PREMIER_LEAGUE_ID = 2021
COMPETITION_DETAIL = '''http://api.football-data.org/v2/competitions/{}'''
TEAM_LIST = '''http://api.football-data.org/v2/competitions/{}/teams'''
TEAM_DETAIL = '''http://api.football-data.org/v2/teams/{}'''
AREA_LIST = 'http://api.football-data.org/v2/areas'


class PermissionException(Exception):
    pass


def get_response(url: str) -> dict:
    headers = {'X-Auth-Token': env('FOOTBALL_API_KEY')}
    print('Getting data from url: [{}]'.format(url))
    r = requests.get(url=url, headers=headers)
    if r.status_code == 200:
        return r.json()
    elif r.status_code == 429:
        search_pattern = re.search(r'\d+', r.json().get('message'))
        wait_time = search_pattern.group()
        print('Token expired, wait [{}]'.format(wait_time))
        time.sleep(int(wait_time))
        return get_response(url)
    elif r.status_code == 403:
        raise PermissionException


def insert_areas():
    response = get_response(AREA_LIST)
    areas = response.get('areas')
    # create world area
    try:
        Area.objects.get(src_id=2267)
    except Area.DoesNotExist:
        area = Area.objects.create(src_id=2267, name='World', code='INT')
        print('Created a area with src_id [{}] and name [{}]'.format(area.src_id, area.name))
    for area in areas:
        create_area(area, areas)


def create_area(area: dict, areas: list):
    src_id = area.get('id')
    try:
        a = Area.objects.get(src_id=src_id)
        # area already created
        a.name = area.get('name')
        a.code = area.get('countryCode')
        a.save()
    except Area.DoesNotExist:
        parent_id = area.get('parentAreaId')
        try:
            parent_area = Area.objects.get(src_id=parent_id)
            # parent area already created
            a = Area.objects.create(src_id=src_id, name=area.get('name'), code=area.get('countryCode'), parent_area=parent_area)
            print('Created a area with src_id [{}] and name [{}]'.format(a.src_id, a.name))
        except Area.DoesNotExist:
            # create parent area
            for i in areas:
                if parent_id == i.get('id'):
                    create_area(i, areas)
                    break
            a = create_area(area, areas)
    return a


def create_competition(src_id: int):
    url = COMPETITION_DETAIL.format(src_id)
    print('Getting competition info from url [{}]'.format(url))
    res = get_response(url)
    # create current season
    current_season = create_season(res.get('currentSeason'))
    seasons = []
    # create history season
    for s in res.get('seasons'):
        created_season = create_season(s)
        seasons.append(created_season)
    area = Area.objects.get(src_id=res.get('area').get('id'))
    try:
        c = Competition.objects.get(src_id=res.get('id'))
        c.name = res.get('name')
        c.code = res.get('code')
        c.area = area
        c.plan = res.get('plan')
        c.current_season = current_season
        c.save()
        # competition already existed
    except Competition.DoesNotExist:
        # create new competition
        c = Competition.objects.create(src_id=res.get('id'), name=res.get('name'), code=res.get('code'), area=area,
                                       plan=res.get('plan'), current_season=current_season)
        print('Created competition with src_id [{}]'.format(c.src_id))
    c.seasons.add(*seasons)
    c.save()
    return c


def create_season(season: dict):
    try:
        start_date = datetime.datetime.strptime(season.get('startDate'), '%Y-%m-%d')
    except TypeError or ValueError:
        start_date = None
    try:
        end_date = datetime.datetime.strptime(season.get('endDate'), '%Y-%m-%d')
    except TypeError or ValueError:
        end_date = None
    try:
        s = Season.objects.get(srd_id=season.get('id'))
        s.start_date = start_date
        s.end_date = end_date
        s.current_match_day = season.get('currentMatchday')
        s.save()
    except Season.DoesNotExist:
        s = Season.objects.create(srd_id=season.get('id'), start_date=start_date, end_date=end_date, current_match_day=season.get('currentMatchday'))
        print('Created season with src_id [{}]'.format(season.get('id')))
    return s


def create_teams(url: str):
    res = get_response(url)
    teams = res.get('teams')
    for team in teams:
        t = get_response(TEAM_DETAIL.format(team.get('id')))
        create_team(t)


def create_team(team: dict):
    area = Area.objects.get(src_id=team.get('area').get('id'))
    active_competitions = team.get('activeCompetitions')
    competitions = []
    for competition in active_competitions:
        src_id = competition.get('id')
        try:
            c = create_competition(src_id)
            competitions.append(c)
        except PermissionException:
            continue
    try:
        t = Team.objects.get(src_id=team.get('id'))
        # team already existed
        t.area = area
        t.name = team.get('name')
        t.tla = team.get('tla')
        t.address = team.get('address')
        t.phone = team.get('phone')
        t.website = team.get('website')
        t.email = team.get('email')
        t.founded = team.get('founded')
        t.colors = team.get('clubColors')
        t.venue = team.get('venue')
        t.save()
    except Team.DoesNotExist:
        # create new team
        t = Team.objects.create(src_id=team.get('id'), area=area, name=team.get('name'), tla=team.get('tla'), address=team.get('address'),
                                phone=team.get('phone'), website=team.get('website'), email=team.get('email'), founded=team.get('founded'),
                                colors=team.get('clubColors'), venue=team.get('venue'))
        print('Created team with src_id [{}]'.format(t.src_id))
    t.active_competitions.add(*competitions)
    t.save()
    members = team.get('squad')
    for member in members:
        create_member(member, t.src_id)
    return t


def create_member(member: dict, team_src_id: int):
    try:
        position = Position.objects.get(name=member.get('position'))
    except Position.DoesNotExist:
        position = None
    role = Role.objects.get(name=member.get('role'))
    try:
        date_of_birth = datetime.datetime.strptime(member.get('dateOfBirth'), '%Y-%m-%dT%H:%M:%SZ')
    except TypeError or ValueError:
        date_of_birth = None
    try:
        m = Member.objects.get(src_id=member.get('id'))
        m.name = member.get('name')
        m.position = position
        m.date_of_birth = date_of_birth
        m.country_of_birth = member.get('countryOfBirth')
        m.nationality = member.get('nationality')
        m.role = role
        m.save()
    except Member.DoesNotExist:
        m = Member.objects.create(src_id=member.get('id'), name=member.get('name'), position=position, date_of_birth=date_of_birth,
                                  country_of_birth=member.get('countryOfBirth'), nationality=member.get('nationality'), role=role)
        print('Created member with src_id [{}]'.format(m.src_id))
    team = Team.objects.get(src_id=team_src_id)
    m.teams.add(team)
    m.save()
    return m


if __name__ == '__main__':
    insert_areas()
    create_competition(PREMIER_LEAGUE_ID)
    create_teams(TEAM_LIST.format(PREMIER_LEAGUE_ID))
